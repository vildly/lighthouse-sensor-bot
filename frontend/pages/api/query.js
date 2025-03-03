export default async function handler(req, res) {
  if (req.method === "POST") {
    try {
      const { question, source_file, prompt_file } = req.body;
      console.log("Sending to backend:", { question, source_file, prompt_file });
      
      const response = await fetch("http://127.0.0.1:5000/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          question,
          source_file,
          prompt_file 
        }),
      });

      if (!response.ok) {
        console.error("Backend error:", response.status, response.statusText);
        throw new Error("Error in Flask endpoint response");
      }

      const data = await response.json();
      console.log("Received from backend:", data);
      
      // Normalize the response format.
      if (data.response) {
        // If backend returns 'response' key, convert it to 'content'.
        res.status(200).json({ content: data.response });
      } else if (data.content) {
        // If backend already returns 'content' key, use it directly.
        res.status(200).json({ content: data.content });
      } else {
        res.status(200).json({ content: "Response received but no content found" });
      }

    } catch (error) {
      console.error(error);
      res.status(500).json({ content: `Internal Server Error: ${error.message}` });
    }
  } else {
    res.status(405).json({ content: "Method Not Allowed" });
  }
}