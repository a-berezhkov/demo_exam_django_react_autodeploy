import React, { useEffect, useState } from "react";
import Loader from "./Loader";

function HistoryComp() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const getHistory = async () => {
    const resp = await fetch(import.meta.env.VITE_URL + "downloads", {
      headers: {
        Authorization: "Bearer " + localStorage.getItem("token"),
      },
    });
    const json = await resp.json();
    setHistory(json.data);
    setLoading(false);
  };
  useEffect(() => {
    getHistory();
  }, []);

  return (
    <div>
      {loading && <Loader></Loader>}
      {history.map((el) => (
        <div className="card">
          <h3>{el.title}</h3>
          <p>{el.author}</p>
          <p>{el.download_date}</p>
        </div>
      ))}
    </div>
  );
}

export default HistoryComp;
