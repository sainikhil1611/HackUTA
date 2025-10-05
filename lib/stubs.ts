/**
 * Mock functions for development and testing
 */

export interface UploadResult {
  fileUrl: string;
  success: boolean;
}

/**
 * Mock S3 presigned upload function
 * Simulates uploading a video file to S3
 */
export async function s3PresignUpload(fileUri: string): Promise<UploadResult> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, Math.random() * 200 + 300));
  
  // Generate a mock file URL
  const timestamp = Date.now();
  const mockFileUrl = `https://mock-s3-bucket.amazonaws.com/videos/video_${timestamp}.mp4`;
  
  console.log(`Mock upload: ${fileUri} -> ${mockFileUrl}`);
  
  return {
    fileUrl: mockFileUrl,
    success: true
  };
}