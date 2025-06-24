import React, { useContext, useEffect, useState } from "react";
import HistoryComp from "../components/HistoryComp";
import UserContext from "../context/UserContext";
import { useNavigate } from "react-router-dom";
import Loader from "../components/Loader";
function UserProfilePage() {
  const [profile, setProfile] = useState(null);
  const [error, setErrors] = useState({});
  const [loading, setLoading] = useState(true)
  const {setUser} = useContext(UserContext)
  const n = useNavigate()

  const getProfile = async () => {
    const resp = await fetch(import.meta.env.VITE_URL + "profile", {
      headers: {
        Authorization: "Bearer " + localStorage.getItem("token"),
      },
    });
    const json = await resp.json();
    setProfile(json.data);
    setLoading(false)
  };

  const changeProfile = async (e) => {
    e.preventDefault();
    const inputs = e.target.querySelectorAll("input");
    setLoading(true)
    let body = {};
    for (const element of inputs) {
      body[element.name] = element.value;
    }
    const resp = await fetch(import.meta.env.VITE_URL + "profile/", {
      method: "PUT",
      headers: {
        Authorization: "Bearer " + localStorage.getItem("token"),
        "content-type": "application/json",
      },
      body: JSON.stringify(body),
    });
    const json = await resp.json();

    if (resp.ok) {
      setProfile(json.data);
      setUser(json.data)
    } else {
      setErrors(json.error.errors);
    }
    setLoading(false)
  };

  const logout = () => {
    localStorage.clear()
    setUser(null)
    n('/')
  }

  useEffect(() => {
    getProfile();
  }, []);
  return (
    <div className="page">
      <div className="center">
        <h1>Профиль</h1>
        {
          loading && <Loader></Loader>
        }
        <button onClick={()=>logout()}>Выход</button>
        <h3>Email: {profile?.email}</h3>
        <p>Имя: {profile?.name}</p>
        <p>Роль: {profile?.role}</p>

        <h2>Изменение профиля</h2>
        <form action="" onSubmit={changeProfile}>
          <input
            type="text"
            name="email"
            placeholder="Email"
            className={error?.email && "error"}
            defaultValue={profile?.email}
          />
          <p className="error">{error?.email}</p>

          <input
            type="text"
            name="name"
            placeholder="Имя"
            className={error?.name && "error"}
            defaultValue={profile?.name}
          />
          <p className="error">{error?.name}</p>
          <input
            type="text"
            name="role"
            placeholder="Роль"
            className={error?.role && "error"}
            defaultValue={profile?.role}
          />
          <p className="error">{error?.role}</p>
          <button type="submit">Изменить</button>
        </form>
        <h2>История</h2>
        <HistoryComp></HistoryComp>
      </div>
      

    </div>
  );
}

export default UserProfilePage;
