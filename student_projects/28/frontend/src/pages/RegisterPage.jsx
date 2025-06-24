import React from "react";
import { useState, useContext } from "react";
import UserContext from "../context/UserContext";
import { useNavigate } from "react-router-dom";

function RegisterPage() {
  const [error, setError] = useState({});
  const { setUser } = useContext(UserContext);
  const [loading, setLoading] = useState(false)
  const n = useNavigate();

  const onReg = async (e) => {
    e.preventDefault();
    setError({});
    setLoading(true)
    const inputs = e.target.querySelectorAll("input");
    let body = {};
    for (const element of inputs) {
      body[element.name] = element.value;
    }

    const resp = await fetch(import.meta.env.VITE_URL + "auth/register", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const json = await resp.json();

    if (resp.ok) {
      localStorage.setItem("user", JSON.stringify(json.data.user));
      localStorage.setItem("token", json.data.token);
      setUser(json.data.user);
      n("/");
    } else {
      setError(json.error.errors);
    }
  };

  return (
    <div className="page">
      <div className="center">
        <h1>Регистрация</h1>
        {
          loading && <Loader></Loader>
        }
        <form action="" onSubmit={onReg}>
          <input
            type="text"
            className={error?.name && "error"}
            name="name"
            placeholder="ФИО"
          />
          <p className="error">{error?.name}</p>
          <input
            type="text"
            className={error?.email && "error"}
            name="email"
            placeholder="Email"
          />
          <p className="error">{error?.email}</p>
          <input
            type="text"
            className={error?.role && "error"}
            name="role"
            placeholder="Должность"
          />
          <p className="error">{error?.role}</p>
          <input
            type="password"
            className={error?.password && "error"}
            name="password"
            placeholder="Password"
          />
          <p className="error">{error?.password}</p>
          <input type="checkbox" />{" "}
          <p>Подтверждаю согласие на обработку личных данных</p>
          <button type="submit">Отправить</button>
        </form>
      </div>
    </div>
  );
}

export default RegisterPage;
