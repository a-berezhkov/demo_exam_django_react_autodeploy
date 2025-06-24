import React from "react";
import HistoryComp from "../components/HistoryComp";

function HistoryPage() {
  return (
    <div className="page">
      <div className="center">
        <h1>История скачивания книг</h1>
        <HistoryComp></HistoryComp>
      </div>
    </div>
  );
}

export default HistoryPage;
