"""
Клиент для Яндекс.Облако Object Storage
Для хранения файлов (аватарки, фото, документы)
"""
import boto3
from botocore.client import Config
import os


class YandexStorage:
    def __init__(self, access_key, secret_key, bucket_name):
        self.bucket_name = bucket_name
        
        # Подключение к Яндекс Object Storage
        self.client = boto3.client(
            's3',
            endpoint_url='https://storage.yandexcloud.net',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4')
        )
    
    def upload_file(self, file_path, object_name):
        """Загружает файл в хранилище."""
        try:
            self.client.upload_file(file_path, self.bucket_name, object_name)
            print(f"✅ Файл загружен: {object_name}")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False
    
    def download_file(self, object_name, file_path):
        """Скачивает файл из хранилища."""
        try:
            self.client.download_file(self.bucket_name, object_name, file_path)
            return True
        except Exception as e:
            print(f"❌ Ошибка скачивания: {e}")
            return False
    
    def get_file_url(self, object_name, expires_in=3600):
        """Получает временную ссылку на файл."""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            print(f"❌ Ошибка получения URL: {e}")
            return None
    
    def upload_avatar(self, user_id, file_path):
        """Загружает аватар пользователя."""
        ext = os.path.splitext(file_path)[1]  # .jpg, .png и т.д.
        object_name = f"users/{user_id}/avatar{ext}"
        success = self.upload_file(file_path, object_name)
        if success:
            return self.get_file_url(object_name, expires_in=31536000)  # 1 год
        return None
    
    def upload_message_file(self, chat_id, file_path, file_name):
        """Загружает файл сообщения."""
        object_name = f"messages/{chat_id}/{file_name}"
        success = self.upload_file(file_path, object_name)
        if success:
            return self.get_file_url(object_name, expires_in=31536000)
        return None
    
    def delete_file(self, object_name):
        """Удаляет файл из хранилища."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления: {e}")
            return False


# Глобальный экземпляр
yandex_storage = None


def init_yandex_storage(access_key, secret_key, bucket_name):
    """Инициализирует Яндекс.Хранилище."""
    global yandex_storage
    yandex_storage = YandexStorage(access_key, secret_key, bucket_name)
    print(f"✅ Яндекс.Хранилище инициализировано (бакет: {bucket_name})")
    return yandex_storage