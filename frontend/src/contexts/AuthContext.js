import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/api';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [isAdmin, setIsAdmin] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [checked, setChecked] = useState(false);

    // Check admin status on app load
    const checkAdminStatus = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/admin/check/`);
            setIsAdmin(response.data.is_admin);
            setUser(response.data.user);
        } catch (error) {
            console.error('Failed to check admin status:', error);
            setIsAdmin(false);
            setUser(null);
        } finally {
            setLoading(false);
            setChecked(true);
        }
    };

    // Login function
    const login = (adminStatus, userData) => {
        setIsAdmin(adminStatus);
        setUser(userData);
    };

    // Logout function
    const logout = async () => {
        try {
            // Call Django logout endpoint if it exists, or just clear local state
            await axios.post(`${API_BASE_URL}/admin/logout/`).catch(() => {
                // Ignore errors - endpoint might not exist
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setIsAdmin(false);
            setUser(null);
        }
    };

    useEffect(() => {
        checkAdminStatus();
    }, []);

    const value = {
        isAdmin,
        user,
        loading,
        checked,
        login,
        logout,
        checkAdminStatus
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;

