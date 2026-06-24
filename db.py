import pymysql
import os
pymysql.install_as_MySQLdb()

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "mysql+pymysql://4LKtZ5VNgC2jej8.root:CKNt2RxrLcC41SrY@gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com:4000/test"

pem_path = r"C:\OneDrive\Desktop\ai career\isrgrootx1.pem"

if os.path.exists(pem_path):
    ssl_args = {
        "ssl_ca": pem_path,
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
    }
else:
    ssl_args = {
        "ssl_verify_cert": False,
        "ssl_verify_identity": False,
    }

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=ssl_args
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()