import mimetypes
import uuid

from django.core.files.storage import Storage
from supabase import create_client

from core.config import SupabaseConfig


class SupabaseStorage(Storage):
    def __init__(self):
        self.client = create_client(SupabaseConfig.SUPABASE_URL, SupabaseConfig.SUPABASE_KEY)
        self.bucket_name = SupabaseConfig.SUPABASE_BUCKET

    def deconstruct(self):
        return (
            'core.storage.SupabaseStorage',  # Change 'core' to your app name
            [],  # args
            {}  # kwargs
        )

    def _save(self, name, content):
        """Save file to Supabase Storage"""
        # Generate unique filename
        ext = name.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        # Determine content type
        content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'

        # Read file content
        file_content = content.read()

        # Upload to Supabase
        self.client.storage.from_(self.bucket_name).upload(
            filename,
            file_content,
            file_options={"content-type": content_type}
        )

        return filename

    def _open(self, name, mode='rb'):
        """Not typically used, but required by Storage interface"""
        raise NotImplementedError("Opening files from Supabase is not supported")

    def exists(self, name):
        """Check if file exists in Supabase Storage"""
        try:
            files = self.client.storage.from_(self.bucket_name).list()
            return any(f['name'] == name for f in files)
        except:
            return False

    def url(self, name):
        """Get public URL for the file"""
        if not name:
            return None
        return self.client.storage.from_(self.bucket_name).get_public_url(name)

    def delete(self, name):
        """Delete file from Supabase Storage"""
        try:
            self.client.storage.from_(self.bucket_name).remove([name])
        except:
            pass

    def size(self, name):
        """Get file size"""
        return 0
