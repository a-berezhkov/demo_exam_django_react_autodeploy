import React from "react";
import { useState, useContext } from "react";
import UserContext from "../context/UserContext";
import { useNavigate } from "react-router-dom";
import Loader from "../components/Loader";

function LoginPage() {
  const [error, setError] = useState({});
  const [details, setDetails] = useState("")
  const { setUser } = useContext(UserContext);
  const [loading, setLoading] = useState(false)
  const n = useNavigate();

  const onReg = async (e) => {
    e.preventDefault();
    setLoading(true)
    setError({});
    const inputs = e.target.querySelectorAll("input");
    let body = {};
    for (const element of inputs) {
      body[element.name] = element.value;
    }

    const resp = await fetch(import.meta.env.VITE_URL + "auth/login", {
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
      setDetails(json.error.details)
    }
    setLoading(false)
  };

  return (
    <div className="page">
      <div className="center">
        <h1>Логин</h1>
        {
          loading && <Loader></Loader>
        }
        <form action="" onSubmit={onReg}>
          <input
            type="text"
            className={error?.email && "error"}
            name="email"
            placeholder="Email"
          />
          <p className="error">{error?.email}</p>
          <input
            type="password"
            className={error?.password && "error"}
            name="password"
            placeholder="Password"
          />
          <p className="error">{error?.password}</p>
          <p className="error">{details}</p>
          <button type="submit">Отправить</button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;
