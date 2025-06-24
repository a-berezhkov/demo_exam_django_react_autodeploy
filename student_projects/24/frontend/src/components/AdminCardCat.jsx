import React, { useState } from "react";

function AdminCardCat({ category, setCategories }) {
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

    const resp = await fetch(
      `http://localhost:8000/api/admin/categories/${category.id}/`,
      {
        method: "PUT",
        headers: {
          "content-type": "application/json",
          Authorization: "Bearer " + localStorage.getItem("token"),
        },
        body: JSON.stringify(body),
      }
    );

    const json = await resp.json();

    if (resp.ok) {
      setCategories((prev) =>
        prev.map((el) => (el.id != category.id ? el : json.data))
      );
      setShow(false);
    } else {
      setError(json.error.errors);
    }
  };

  const onDelete = async () => {
    const resp = await fetch(
      `http://localhost:8000/api/admin/categories/${category.id}/`,
      {
        method: "DELETE",
        headers: {
          Authorization: "Bearer " + localStorage.getItem("token"),
        },
      }
    );

    if (resp.ok) {
      setCategories((prev) =>
        prev.filter((e) => {
          return e.id != category.id;
        })
      );
    }
  };

  return (
    <div className="card">
      <p>{category.id}</p>
      <h3>{category.name}</h3>
      <button onClick={() => setShow((prev) => !prev)}>Изменение</button>
      {show && (
        <>
          <form action="" onSubmit={onChange}>
            <input
              type="text"
              name="name"
              defaultValue={category.name}
              className={error?.name && "error"}
            />
            <p className="error">{error?.name}</p>
            <button type="submit">Изменить</button>
          </form>
        </>
      )}
      <button onClick={() => onDelete()}>Удалить</button>
    </div>
  );
}

export default AdminCardCat;
