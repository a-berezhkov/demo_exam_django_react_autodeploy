import React, { useEffect, useState } from "react";
import AdminCardCat from "../components/AdminCardCat";

function AdminPage() {
  const [cats, setCats] = useState([]);

  const getCats = async () => {
    const resp = await fetch(import.meta.env.VITE_URL + "admin/categories/", {
      headers: {
        'Authorization': "Bearer " + localStorage.getItem('token')
      }
    });
    const json = await resp.json();
    if (resp.ok) {
      setCats(json.data);
    }
  };

  useEffect(() => {
    getCats();
  }, []);

  return (<div className="page">
    <div className="center">
      <h1>Общие настройки</h1>
      <h2>Категории</h2>
      {
        cats.map(el=>(
          <AdminCardCat category={el} setCategories={setCats}></AdminCardCat>
        ))
      }

    </div>


  </div>);
}

export default AdminPage;
