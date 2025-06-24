import { createBrowserRouter } from "react-router-dom";
import Layout from "../layout/Layout";
import Main from "../pages/Main";
import DetailsPage from "../pages/DetailsPage";
import AdminPage from "../pages/AdminPage";
import RegisterPage from "../pages/RegisterPage";
import LoginPage from "../pages/LoginPage";
import UserProfilePage from "../pages/UserProfilePage";
import TeacherPage from "../pages/TeacherPage";
import HistoryPage from "../pages/HistoryPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout></Layout>,
    children: [
      {
        path: "/",
        element: <Main></Main>,
      },
      {
        path: "/:id",
        element: <DetailsPage></DetailsPage>,
      },
      {
        path: "/admin",
        element: <AdminPage></AdminPage>,
      },
      {
        path: "/register",
        element: <RegisterPage></RegisterPage>,
      },
      {
        path: "/login",
        element: <LoginPage></LoginPage>,
      },
      {
        path: "/user-profile",
        element: <UserProfilePage></UserProfilePage>,
      },
      {
        path: "teacher",
        element: <TeacherPage></TeacherPage>,
      },
      {
        path: "history",
        element: <HistoryPage></HistoryPage>,
      },
      {
        path: "admin",
        element: <AdminPage></AdminPage>,
      },
    ],
  },
]);

export default router;
