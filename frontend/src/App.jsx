import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./components/AppLayout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import PublicOnlyRoute from "./components/PublicOnlyRoute.jsx";
import Chat from "./pages/Chat.jsx";
import Databases from "./pages/Databases.jsx";
import DatabaseQuery from "./pages/DatabaseQuery.jsx";
import Documents from "./pages/Documents.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";

function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Navigate to="chat" replace />} />
          <Route path="chat" element={<Chat />} />
          <Route path="chat/:conversationId" element={<Chat />} />
          <Route path="documents" element={<Documents />} />
          <Route path="databases" element={<Databases />} />
          <Route path="databases/:connectionId" element={<DatabaseQuery />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
