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
import DatabasesInfo from "./pages/marketing/Databases.jsx";
import Docs from "./pages/marketing/Docs.jsx";
import Product from "./pages/marketing/Product.jsx";
import Register from "./pages/Register.jsx";

function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      {/* Content pages, not auth gates — reachable whether or not the
          visitor is logged in (e.g. a signed-in user checking /docs). */}
      <Route path="/product" element={<Product />} />
      <Route path="/databases" element={<DatabasesInfo />} />
      <Route path="/docs" element={<Docs />} />

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
