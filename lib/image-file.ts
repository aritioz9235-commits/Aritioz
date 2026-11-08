export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'] as const;

type ImageFileMetadata = Pick<File, 'type' | 'size'>;

export function validateImageFile(file: ImageFileMetadata): void {
  if (!(ALLOWED_IMAGE_TYPES as readonly string[]).includes(file.type)) {
    throw new Error('Choose a JPEG, PNG, or WebP image.');
  }
  if (file.size <= 0 || file.size > MAX_IMAGE_BYTES) {
    throw new Error('Image must be smaller than 5 MB.');
  }
}

export async function readImageFile(file: File): Promise<string> {
  validateImageFile(file);
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () =>
      typeof reader.result === 'string'
        ? resolve(reader.result)
        : reject(new Error('The selected image could not be read.'));
    reader.onerror = () => reject(new Error('The selected image could not be read.'));
    reader.readAsDataURL(file);
  });
}
