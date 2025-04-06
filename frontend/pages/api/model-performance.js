import process from 'process';

export default async function handler(req, res) {
  const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL;
  const modelType = req.query.type;
  
  const params = new URLSearchParams();
  if (modelType) {
    params.append('type', modelType);
  }
  
  try {
    const response = await fetch(`${SERVER_URL}/api/model-performance?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Error fetching model performance: ${response.statusText}`);
    }
    
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error('Error fetching model performance:', error);
    res.status(500).json({ error: 'Failed to fetch model performance data' });
  }
} 