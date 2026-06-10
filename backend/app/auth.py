from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import User, UserRole
import os
import pandas as pd


def load_users_from_csv():
    """Load all employees from HR dataset"""
    users = {}
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "hr", "hr_data.csv")

    try:
        df = pd.read_csv(csv_path)

        for _, row in df.iterrows():
            email = str(row.get("email", "")).strip()
            if not email or email == "nan":
                continue

            # Exact department name matching
            dept = str(row.get("department", "")).strip()

            if dept == "Finance":
                role = UserRole.FINANCE
            elif dept == "Marketing":
                role = UserRole.MARKETING
            elif dept == "HR":
                role = UserRole.HR
            elif dept in ["Technology", "Quality Assurance", "Data"]:
                role = UserRole.ENGINEERING
            elif dept in ["Sales", "Business", "Operations", "Compliance", "Risk", "Product", "Design"]:
                role = UserRole.EMPLOYEE
            else:
                role = UserRole.EMPLOYEE

            users[email] = {
                "username": email,
                "password": "password123",
                "role": role,
                "name": str(row.get("full_name", email))
            }

        print(f"✅ Loaded {len(users)} users from HR CSV")

    except Exception as e:
        print(f"⚠️ Could not load CSV: {e}")

    return users


# Load all employees from CSV
USERS_DB = load_users_from_csv()

# Add CEO manually
USERS_DB["ceo@fintechco.com"] = {
    "username": "ceo@fintechco.com",
    "password": "password123",
    "role": UserRole.EXECUTIVE,
    "name": "CEO User"
}


class AuthHandler:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-12345")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        if username not in USERS_DB:
            return None

        user_data = USERS_DB[username]

        if password != user_data["password"]:
            return None

        return User(
            username=username,
            role=user_data["role"],
            name=user_data["name"],
            email=username
        )

    def create_token(self, user: User) -> str:
        """Create JWT token"""
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user.username,
            "role": user.role.value,
            "name": user.name,
            "exp": expire
        }
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def decode_token(self, token: str) -> Dict:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
    ) -> User:
        """Get current user from token"""
        if not credentials:
            return User(
                username="employee@fintechco.com",
                role=UserRole.EMPLOYEE,
                name="Guest User"
            )

        token = credentials.credentials
        payload = self.decode_token(token)

        username = payload.get("sub")
        role = payload.get("role")
        name = payload.get("name", username)

        return User(
            username=username,
            role=UserRole(role) if role else UserRole.EMPLOYEE,
            name=name
        )