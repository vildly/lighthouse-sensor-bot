import { useState } from "react";

// This is a simple form that allows the user to ask a question and receive a response.
export default function QuestionForm() {
  const [question, setQuestion] = useState("");
  const [content, setContent] = useState(null);

  const askQuestion = async () => {
    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      console.log(response)

      if (!response.ok) throw new Error("Failed to get response");

      const data = await response.json();
      setContent(data.content || "No content available.");
    } catch (error) {
      console.error("Error fetching response:", error);
      setContent("Failed to fetch response.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4">Ask a Question</h1>

        <textarea
          rows="4"
          className="w-full p-2 border border-gray-200 rounded-md mb-4"
          placeholder="Type your question here..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        ></textarea>

        <button
          onClick={askQuestion}
          className="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600"
        >
          Send
        </button>

        {content && (
          <div className="bg-gray-50 p-4 mt-4 rounded-md">
            <h2 className="font-semibold">Response:</h2>
            <pre className="whitespace-pre-wrap">{content}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
