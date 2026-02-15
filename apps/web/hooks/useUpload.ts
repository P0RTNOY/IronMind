import { useState } from 'react';
import { apiFetch } from '../lib/api';
import { UploadSignResponse } from '../types';

export function useUpload() {
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const uploadFile = async (
        file: File,
        kind: 'cover' | 'plan_pdf'
    ): Promise<UploadSignResponse | null> => {
        setUploading(true);
        setError(null);

        try {
            // 1. Get Signed URL
            const signRes = await apiFetch<UploadSignResponse>('/admin/uploads/sign', {
                method: 'POST',
                body: JSON.stringify({
                    kind,
                    filename: file.name,
                    contentType: file.type
                })
            });

            if (signRes.status !== 200 || !signRes.data) {
                throw new Error(signRes.error?.detail || 'Failed to get signed URL');
            }

            const { uploadUrl, publicUrl, objectPath } = signRes.data;

            // 2. Upload to GCS
            const uploadRes = await fetch(uploadUrl, {
                method: 'PUT',
                body: file,
                headers: {
                    'Content-Type': file.type
                }
            });

            if (!uploadRes.ok) {
                throw new Error('Failed to upload file to storage');
            }

            setUploading(false);
            return { uploadUrl, publicUrl, objectPath };

        } catch (err: any) {
            console.error("Upload error:", err);
            setError(err.message || "Upload failed");
            setUploading(false);
            return null;
        }
    };

    return { uploadFile, uploading, error };
}
