"""Yandex Object Storage для фото и видео."""
import os
import boto3
from botocore.client import Config
from typing import Optional, List
from datetime import datetime

class YandexStorage:
    def __init__(self):
        self.client = None
        self.bucket = None
        self.initialized = False
    
    def init(self):
        """Инициализирует подключение к Yandex Storage."""
        try:
            self.session = boto3.session.Session()
            self.client = self.session.client(
                service_name='s3',
                endpoint_url='https://storage.yandexcloud.net',
                aws_access_key_id=os.getenv('YANDEX_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('YANDEX_SECRET_KEY'),
                config=Config(signature_version='s3v4')
            )
            self.bucket = os.getenv('YANDEX_BUCKET_NAME', 'ten-dem-files')
            self.initialized = True
            print(f"✅ Yandex Storage подключён (бакет: {self.bucket})")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к Yandex Storage: {e}")
            self.initialized = False
            return False
    
    def upload_file(self, file_path: str, folder: str = "messages") -> Optional[str]:
        """Загружает файл и возвращает URL."""
        if not self.initialized:
            self.init()
        
        if not self.initialized or not os.path.exists(file_path):
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{os.path.basename(file_path)}"
            key = f"{folder}/{filename}"
            
            self.client.upload_file(file_path, self.bucket, key)
            
            url = f"https://storage.yandexcloud.net/{self.bucket}/{key}"
            print(f"✅ Файл загружен: {url}")
            return url
        except Exception as e:
            print(f"❌ Ошибка загрузки файла: {e}")
            return None

storage = YandexStorage()

def init_yandex_storage():
    """Инициализирует Yandex Storage."""
    return storage.init()

def upload_file(file_path: str, folder: str = "messages") -> Optional[str]:
    """Загружает файл в Yandex Storage."""
    return storage.upload_file(file_path, folder)