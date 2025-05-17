import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "../ProtectedRoute";

import Login from "./components/Login";
import Registration from "./components/Registration";
import Messaging from "./components/Messaging";
import GroupMessaging from "./components/GroupMessaging";
import Profile from "./components/Profile";
import UserProfilePage from "./components/UserProfilePage";
import Navbar from "./components/Navbar";
import MarketPlace from "./components/MarketPlace";
import Home from "./Home";
import DeleteAccount from "./components/DeleteAccount";
import BlockedUsers from "./components/BlockedUsers";
import ForgotPassword from './components/ForgotPassword';


function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <div className="app">
                    <Navbar />
                    <div className="main-content full-width-page">
                        <Routes>
                            <Route path="/" element={<Login />} />
                            <Route path="/login" element={<Login />} />
                            <Route
                                path="/register"
                                element={<Registration />}
                            />
                            <Route path="/forgot-password" element={<ForgotPassword />} />

                            <Route element={<ProtectedRoute />}>
                                <Route path="/home" element={<Home />} />
                                <Route path="/profile" element={<Profile />} />
                                <Route
                                    path="/users/:username"
                                    element={<UserProfilePage />}
                                />
                                <Route
                                    path="/messages"
                                    element={<Messaging />}
                                />
                                <Route
                                    path="/groups"
                                    element={<GroupMessaging />}
                                />
                                <Route
                                    path="/market"
                                    element={<MarketPlace />}
                                />
                                <Route
                                    path="/delete-account"
                                    element={<DeleteAccount />}
                                />
                                <Route
                                    path="/blocked-users"
                                    element={<BlockedUsers />}
                                />
                                <Route
                                    path="/blocked-users"
                                    element={<BlockedUsers />}
                                />
                            </Route>
                        </Routes>
                    </div>
                </div>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
