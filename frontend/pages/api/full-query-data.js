import process from 'process';

const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL;

export default async function handler(req, res) {
  try {
    const response = await fetch(`${SERVER_URL}/api/full-query-data`);
    
    if (!response.ok) {
      throw new Error(`Error fetching query history: ${response.statusText}`);
    }
    
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error('Error fetching query history:', error);
    res.status(500).json({ error: 'Failed to fetch query history data' });
  }
} 