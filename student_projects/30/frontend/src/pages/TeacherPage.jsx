import React, { useEffect, useState } from "react";
import BookCardAdmin from "../components/BookCardAdmin";

function TeacherPage() {
  const [books, setBooks] = useState([]);
  const [error, setError] = useState({});
  const getBooks = async () => {
    const resp = await fetch(import.meta.env.VITE_URL + "books/");
    const json = await resp.json();
    if (resp.ok) {
      setBooks(json.data);
    }
  };

  useEffect(() => {
    getBooks();
  }, []);
  const onChange = async (e) => {
    e.preventDefault();
    setError({});
    const inputs = e.target.querySelectorAll("input");
    let body = {};
    for (const element of inputs) {
      body[element.name] = element.value;
    }

    const resp = await fetch(`http://localhost:8000/api/books/`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        Authorization: "Bearer " + localStorage.getItem("token"),
      },
      body: JSON.stringify(body),
    });

    const json = await resp.json();

    if (resp.ok) {
      setBooks(prev=>[...prev, json.data]);
    } else {
      setError(json.error.errors);
    }
  };

  return (
    <div className="page">
      <div className="center">
        <h1>Каталог книг преподавателя</h1>
        <h3>Создание</h3>
        <form action="" onSubmit={onChange}>
          <input
            type="text"
            name="title"
            className={error?.title && "error"}
            placeholder="Название"
          />
          <p className="error">{error?.title}</p>
          <input
            type="text"
            name="author"
            placeholder="Автор"
            className={error?.author && "error"}
          />
          <p className="error">{error?.author}</p>
          <input
            type="text"
            name="cover"
            className={error?.cover && "error"}
            placeholder="Обложка"
          />
          <p className="error">{error?.cover}</p>
          <input
            type="text"
            name="category"
            placeholder="Category"
            className={error?.category && "error"}
          />
          <p className="error">{error?.category}</p>
          <button type="submit">Добавить</button>
        </form>

        {books.map((el) => (
          <BookCardAdmin book={el} setBooks={setBooks}></BookCardAdmin>
        ))}
        {books.length == 0 && <h2>Книг нет</h2>}
      </div>
    </div>
  );
}

export default TeacherPage;
