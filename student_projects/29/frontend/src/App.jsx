import { useEffect, useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
import { RouterProvider } from "react-router-dom";
import router from "./router/Router";
import UserContext from "./context/UserContext";

function App() {
  const [user, setUser] = useState(null);

  const getProfile = async () => {
    const resp = await fetch(import.meta.env.VITE_URL + "profile", {
      headers: {
        Authorization: "Bearer " + localStorage.getItem("token"),
      },
    });
    const json = await resp.json();
    setUser(json.data);
  };

  useEffect(() => {
    getProfile();
  }, []);

  return (
    <>
      <UserContext.Provider value={{ user, setUser }}>
        <RouterProvider router={router}></RouterProvider>
      </UserContext.Provider>
    </>
  );
}

export default App;
