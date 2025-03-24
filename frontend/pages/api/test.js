import process from 'process';

const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL;

export default async function handler(req, res) {
    try {


      const response = await fetch(`${SERVER_URL}/api/test`);
      
      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }
      
      const data = await response.json();
      res.status(200).json(data);
    } catch (error) {
      console.error("Error testing backend connection:", error);
      res.status(500).json({ 
        content: "Failed to connect to backend", 
        error: error.message 
      });
    }
  }