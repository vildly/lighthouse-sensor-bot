// Description: This file is the API endpoint for the frontend to query the backend server.
export default async function handler(req, res) {
  if (req.method === "POST") {
    try {
      const { question } = req.body;
      const response = await fetch("http://127.0.0.1:5000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      console.log(response)

      if (!response.ok) throw new Error("Error in Flask endpoint response");

      const data = await response.json();
      res.status(200).json(data);

    } catch (error) {
      console.error(error);
      res.status(500).json({ response: "Internal Server Error" });
    }
  } else {
    res.status(405).json({ response: "Method Not Allowed" });
  }
}
