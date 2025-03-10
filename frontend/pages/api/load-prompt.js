import fs from 'fs';
import path from 'path';

export default async function handler(req, res) {
  try {
    // Path to the prompt file.
    const promptPath = path.join(process.cwd(), 'public', 'prompt.txt');
    
    // Check if file exists.
    if (!fs.existsSync(promptPath)) {
      return res.status(404).json({ error: "Prompt file not found" });
    }
    
    // Read the file content.
    const content = fs.readFileSync(promptPath, 'utf8');
    
    res.status(200).json({ content });
  } catch (error) {
    console.error("Error loading prompt:", error);
    res.status(500).json({ error: "Failed to load prompt" });
  }
} 