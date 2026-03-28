import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "@/pages/Dashboard";
import Collect from "@/pages/Collect";
import CollectionDetail from "@/pages/CollectionDetail";
import GameList from "@/pages/GameList";
import GameDetailPage from "@/pages/GameDetail";
import GameEdit from "@/pages/GameEdit";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background">
          <nav className="border-b p-4">
            <div className="container mx-auto flex gap-4">
              <Link to="/" className="font-bold">TousLesJeux</Link>
              <Link to="/games">Jeux</Link>
              <Link to="/collect">Collecter</Link>
            </div>
          </nav>
          <main className="container mx-auto p-4">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/collect" element={<Collect />} />
              <Route path="/collections/:id" element={<CollectionDetail />} />
              <Route path="/games" element={<GameList />} />
              <Route path="/games/:id" element={<GameDetailPage />} />
              <Route path="/games/:id/edit" element={<GameEdit />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
