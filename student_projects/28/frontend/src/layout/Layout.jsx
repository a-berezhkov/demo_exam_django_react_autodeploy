import React, { useContext } from "react";
import { Link, Outlet } from "react-router-dom";
import UserContext from "../context/UserContext";

function Layout() {
  const { user } = useContext(UserContext);
  return (
    <>
      <header>
        <nav>
          <Link to={"/"}>Цифровая библиотека</Link>

          {!user ? (
            <>
              <Link to={"/register"}>Регистрация</Link>
              <Link to={"/login"}>Логин</Link>
            </>
          ) : (
            <>
              <Link to={"/user-profile"}>Профиль пользователя</Link>
              <Link to={"/history"}>История загрузок</Link>
            </>
          )}
          {(user && user?.role == "teacher" || user?.role == "Учитель" || user?.role == "admin") ? (
            <>
              <Link to={"/teacher"}>Каталог книг преподавателя</Link>
            
            
            </>
          ) : (
            <></>
          )}

          {(user && user?.role == "admin" ) ? (
            <>
              <Link to={"/admin"}>Общие настройки библиотеки</Link>
            </>
          ) : (
            <></>
          )}
        </nav>
      </header>
      <main>
        <Outlet></Outlet>
      </main>
    </>
  );
}

export default Layout;
