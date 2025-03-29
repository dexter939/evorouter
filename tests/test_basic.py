import unittest
from app import app

class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
        
    def test_home_status_code(self):
        # Verifica che l'app sia configurata correttamente
        result = self.client.get('/')
        # Verifica che lo status code sia 302 (redirect) poiché 
        # l'homepage richiederebbe login
        self.assertEqual(result.status_code, 302)  # 302 redirect a login

    def test_database_is_initialized(self):
        # Verifica che il database sia stato inizializzato
        with self.app.app_context():
            from app import db
            self.assertTrue(db is not None)

if __name__ == '__main__':
    unittest.main()