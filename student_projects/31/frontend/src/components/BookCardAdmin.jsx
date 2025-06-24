import React, { useState } from "react";

function BookCardAdmin({ book, setBooks }) {
  const [show, setShow] = useState(false);
  const [error, setError] = useState({});
  const onChange = async (e) => {
    e.preventDefault();
    setError({});
    const inputs = e.target.querySelectorAll("input");
    let body = {};
    for (const element of inputs) {
      body[element.name] = element.value;
    }

    const resp = await fetch(`http://localhost:8000/api/books/${book.id}/`, {
      method: "PUT",
      headers: {
        "content-type": "application/json",
        Authorization: "Bearer " + localStorage.getItem("token"),
      },
      body: JSON.stringify(body),
    });

    const json = await resp.json();

    if (resp.ok) {
      setBooks(prev=>prev.map(el=>el.id != book.id ? el : json.data));
      setShow(false);
    } else {
      setError(json.error.errors);
    }
  };

  const onDelete = async () => {
    const resp = await fetch(`http://localhost:8000/api/books/${book.id}/`, {
      method: "DELETE",
      headers: {
        Authorization: "Bearer " + localStorage.getItem("token"),
      },
    });

    if (resp.ok) {
        console.log(book.id);
        
      setBooks((prev) => prev.filter((e) => {
        return e.id != book.id
      }));
    }
  };

  return (
    <div className="card">
        {book.id}
      <h3>Название: {book.title}</h3>
      <p>Автор: {book.author}</p>
      <p>Категория: {book.category.name}</p>
      <button onClick={() => setShow((prev) => !prev)}>Изменение</button>

      {show && (
        <>
          <form action="" onSubmit={onChange}>
            <input type="text" name="title" defaultValue={book.title}  className={error?.title && "error"}/>
            <p className="error">{error?.title}</p>
            <input type="text" name="author" defaultValue={book.author} className={error?.author && "error"}/>
            <p className="error">{error?.author}</p>
            <button type="submit">Изменить</button>
          </form>
        </>
      )}
      <img className="imagebook" src={book.cover} alt="img" />
      <button onClick={() => onDelete()}>Удалить</button>
    </div>
  );
}

export default BookCardAdmin;
