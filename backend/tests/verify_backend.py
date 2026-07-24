import unittest
import json
import os
import sys

# Add workspace directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import app
from backend.firebase.db_manager import db_manager

class BackendAPITests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        # Insert a test user manually into DB manager to test login
        self.test_user_email = "test.verification@customwear.io"
        self.test_user_pass = "verification123"
        
        # Clean existing test user if any
        existing = db_manager.get_user_by_email(self.test_user_email)
        if existing:
            # Delete user (mock mode delete is direct)
            if not db_manager.firebase_enabled:
                db = db_manager._load_local_db()
                if existing["id"] in db["users"]:
                    del db["users"][existing["id"]]
                    db_manager._save_local_db(db)

    def test_1_get_products(self):
        print("Testing GET /api/products...")
        response = self.app.get('/api/products')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0, "Products list should have seeded products")
        print(f"Successfully fetched {len(data)} products.")

    def test_2_user_registration_and_login(self):
        print("Testing user registration and login endpoints...")
        
        # 1. Register
        reg_payload = {
            "name": "Test Verification User",
            "email": self.test_user_email,
            "password": self.test_user_pass
        }
        response = self.app.post('/api/auth/register', 
                                 data=json.dumps(reg_payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("token", data)
        self.assertEqual(data["user"]["email"], self.test_user_email)
        
        # 2. Login
        login_payload = {
            "email": self.test_user_email,
            "password": self.test_user_pass
        }
        response = self.app.post('/api/auth/login', 
                                 data=json.dumps(login_payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        login_data = json.loads(response.data)
        self.assertIn("token", login_data)
        token = login_data["token"]
        
        # 3. Fetch profile with token
        headers = {"Authorization": f"Bearer {token}"}
        profile_res = self.app.get('/api/auth/profile', headers=headers)
        self.assertEqual(profile_res.status_code, 200)
        profile_data = json.loads(profile_res.data)
        self.assertEqual(profile_data["email"], self.test_user_email)
        
        print("Successfully validated Register, Login, and Profile details.")

    def test_3_order_flow(self):
        print("Testing checkout order generation and mock payment...")
        
        # Setup login session
        reg_payload = {
            "name": "Order Tester",
            "email": "order.tester@customwear.io",
            "password": "testerpassword"
        }
        self.app.post('/api/auth/register', 
                      data=json.dumps(reg_payload),
                      content_type='application/json')
                      
        login_res = self.app.post('/api/auth/login', 
                                  data=json.dumps({"email": "order.tester@customwear.io", "password": "testerpassword"}),
                                  content_type='application/json')
        token = json.loads(login_res.data)["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get a product ID
        prod_res = self.app.get('/api/products')
        prod_id = json.loads(prod_res.data)[0]["id"]
        
        # Create order
        order_payload = {
            "items": [
                {
                    "product_id": prod_id,
                    "name": "Test Tee",
                    "price": 320,
                    "quantity": 2,
                    "size": "L",
                    "color": "White",
                    "print_style": "plain"
                }
            ],
            "shipping_address": {
                "name": "Order Tester",
                "phone": "9999999999",
                "email": "order.tester@customwear.io",
                "address": "123 Verification Street",
                "city": "Salem",
                "district": "Salem",
                "state": "Tamil Nadu",
                "pin": "636001"
            }
        }
        
        order_res = self.app.post('/api/orders', 
                                  data=json.dumps(order_payload),
                                  content_type='application/json',
                                  headers=headers)
        self.assertEqual(order_res.status_code, 201)
        order_data = json.loads(order_res.data)["order"]
        order_id = order_data["id"]
        
        # Verify order state is Ordered
        self.assertEqual(order_data["status"], "Ordered")
        self.assertEqual(order_data["payment_status"], "Pending")
        
        # Test get pay QR details
        pay_res = self.app.post(f'/api/orders/{order_id}/pay', headers=headers)
        self.assertEqual(pay_res.status_code, 200)
        pay_data = json.loads(pay_res.data)
        self.assertIn("qr_code_url", pay_data)
        self.assertIn("upi_link", pay_data)
        
        # Simulate payment success
        confirm_res = self.app.post(f'/api/orders/{order_id}/pay', 
                                    data=json.dumps({"simulate_success": True}),
                                    content_type='application/json',
                                    headers=headers)
        self.assertEqual(confirm_res.status_code, 200)
        confirm_data = json.loads(confirm_res.data)["order"]
        self.assertEqual(confirm_data["payment_status"], "Paid")
        
        # Test invoice retrieval via query parameter Authorization
        invoice_res = self.app.get(f'/api/orders/{order_id}/invoice?Authorization=Bearer%20{token}')
        self.assertEqual(invoice_res.status_code, 200)

        print("Successfully validated Order placement and UPI Payment simulation.")

    def test_4_token_verification_and_query_param_auth(self):
        print("Testing token error handling for missing/invalid tokens...")
        
        # 1. Missing Authorization header
        res1 = self.app.get('/api/auth/profile')
        self.assertEqual(res1.status_code, 401)
        data1 = json.loads(res1.data)
        self.assertEqual(data1["message"], "Token is missing!")

        # 2. String literal "undefined" or "null" token
        res2 = self.app.get('/api/auth/profile', headers={"Authorization": "Bearer undefined"})
        self.assertEqual(res2.status_code, 401)
        data2 = json.loads(res2.data)
        self.assertEqual(data2["message"], "Token is missing!")

        res3 = self.app.get('/api/auth/profile', headers={"Authorization": "Bearer null"})
        self.assertEqual(res3.status_code, 401)
        data3 = json.loads(res3.data)
        self.assertEqual(data3["message"], "Token is missing!")
        
        print("Successfully verified token error handling and edge cases.")

if __name__ == '__main__':
    unittest.main()
