import React, { useEffect, useState } from "react";
import logo from "./logo.svg";
import "./App.css";
import img from "./plant.jpg";
import { Code, dracula } from "react-code-blocks";

interface Path {
  line: number;
  content: string;
}

interface Todos {
  [key: string]: Path[];
}

function App() {
  const [todos, setTodos] = useState<Todos>({});

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws");

    socket.onopen = () => {
      console.log("WebSocket connection established");
    };

    socket.onmessage = (event) => {
      console.log(event.data);
      const data = JSON.parse(event.data);
      if (data !== undefined) {
        console.log(data);
        setTodos(data);
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    socket.onclose = () => {
      console.log("WebSocket connection closed");
    };

    return () => {
      socket.close();
    };
  }, [setTodos]);

  return (
    <div>
      <div className="content-bg">
        <img className="bg-image" src={img} />
      </div>

      <div className="content">
        <div className="content-title">TDDD</div>

        <div className="content-items">
          {Object.entries(todos).map(([key, todo], index) => (
            <div key={index} className="content-item">
              <h2>{key}</h2>
              <div className="todo-container">
                {todo.map((item, idx) => (
                  <div className="todo-item" key={idx}>
                    <Code
                      text={item.content}
                      language="c"
                      startingLineNumber={item.line + 1}
                      theme={dracula}
                      showLineNumbers
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="content-footer">
          <div>Made with ❤️ in Rennes</div>
          <div className="image-credit">
            Photo by{" "}
            <a href="https://unsplash.com/@scottwebb?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">
              Scott Webb
            </a>{" "}
            on{" "}
            <a href="https://unsplash.com/photos/green-plant-hDyO6rr3kqk?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">
              Unsplash
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
