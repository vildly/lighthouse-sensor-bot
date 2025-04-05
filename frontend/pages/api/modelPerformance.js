import process from 'process';

export async function getModelPerformance(modelType = null) {
  const params = new URLSearchParams();
  if (modelType) {
    params.append('type', modelType);
  }
  
  const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL;
  
  const response = await fetch(`${SERVER_URL}/api/model-performance?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Error fetching model performance: ${response.statusText}`);
  }
  
  return response.json();
}