import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const login = async () => {
        try {
            const response = await axios.get("/api/profile/", {
                withCredentials: true,
            });
            setUser(response.data);
            return response.data;
        } catch (error) {
            // Only log non-401 errors
            if (
                !error.response ||
                (error.response.status !== 401 &&
                    error.response.status !== 400 &&
                    error.response.status !== 403)
            ) {
                console.error("Profile fetch error:", error);
            }
            setUser(null);
            if (
                error.response &&
                error.response.status !== 401 &&
                error.response.status !== 400 &&
                error.response.status !== 403
            ) {
                throw new Error("Failed to load profile");
            }
            return null;
        }
    };

    const logout = async () => {
        try {
            // Extract CSRF token from cookies
            const csrfCookie = document.cookie
                .split("; ")
                .find((row) => row.startsWith("csrftoken="));
            const csrfToken = csrfCookie ? csrfCookie.split("=")[1] : "";

            await axios.post(
                "/api/logout/",
                {},
                {
                    withCredentials: true,
                    headers: {
                        "X-CSRFToken": csrfToken,
                    },
                },
            );
        } catch (error) {
            // Only log non-auth related errors
            if (
                !error.response ||
                (error.response.status !== 401 &&
                    error.response.status !== 400 &&
                    error.response.status !== 403)
            ) {
                console.error("Logout error:", error);
            }
        } finally {
            setUser(null);
        }
    };

    // Initial auth check
    useEffect(() => {
        const checkAuth = async () => {
            try {
                await login();
            } catch (error) {
                setUser(null);
            } finally {
                setLoading(false);
            }
        };
        checkAuth();
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
