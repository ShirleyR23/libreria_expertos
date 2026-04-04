/**
 * Servicio de API para comunicación con el backend
 * Todas las funciones usan fetch con JWT
 */

const API_URL =
  import.meta.env.PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Obtiene el token JWT del localStorage
 */
const getToken = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("token");
  }
  return null;
};

/**
 * Headers por defecto para peticiones autenticadas
 */
const getHeaders = (includeAuth = true) => {
  const headers = {
    "Content-Type": "application/json",
  };

  if (includeAuth) {
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  return headers;
};

/**
 * Maneja errores de la API
 */
const handleResponse = async (response) => {
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Error en la petición");
  }

  return data;
};

// ============================================================
// AUTENTICACIÓN
// ============================================================

export const login = async (email, password) => {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: getHeaders(false),
    body: JSON.stringify({ email, password }),
  });

  return handleResponse(response);
};

export const registerClient = async (userData) => {
  const response = await fetch(`${API_URL}/auth/register-client`, {
    method: "POST",
    headers: getHeaders(false),
    body: JSON.stringify(userData),
  });

  return handleResponse(response);
};

export const getCurrentUser = async () => {
  const response = await fetch(`${API_URL}/auth/me`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

// ============================================================
// LIBROS
// ============================================================

export const getBooks = async (params = {}) => {
  const queryParams = new URLSearchParams();

  if (params.categoria_id)
    queryParams.append("categoria_id", params.categoria_id);
  if (params.search) queryParams.append("search", params.search);
  if (params.solo_disponibles) queryParams.append("solo_disponibles", "true");
  if (params.skip) queryParams.append("skip", params.skip);
  if (params.limit) queryParams.append("limit", params.limit);

  const response = await fetch(`${API_URL}/books/catalog?${queryParams}`, {
    headers: getHeaders(false), // Catálogo es público
  });

  return handleResponse(response);
};

export const getBookById = async (id) => {
  const response = await fetch(`${API_URL}/books/${id}`, {
    headers: getHeaders(false),
  });

  return handleResponse(response);
};

export const getCategories = async () => {
  const response = await fetch(`${API_URL}/books/categories`, {
    headers: getHeaders(false),
  });

  return handleResponse(response);
};

export const getBestsellers = async (limit = 10) => {
  const response = await fetch(`${API_URL}/books/bestsellers?limit=${limit}`, {
    headers: getHeaders(false),
  });

  return handleResponse(response);
};

export const getInventory = async () => {
  const response = await fetch(`${API_URL}/books/inventory/all`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

export const createBook = async (bookData) => {
  const response = await fetch(`${API_URL}/books/`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(bookData),
  });

  return handleResponse(response);
};

export const updateBook = async (id, bookData) => {
  const response = await fetch(`${API_URL}/books/${id}`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(bookData),
  });

  return handleResponse(response);
};

export const deleteBook = async (id) => {
  const response = await fetch(`${API_URL}/books/${id}`, {
    method: "DELETE",
    headers: getHeaders(),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Error al eliminar el libro");
  }

  return true;
};

// ============================================================
// VENTAS
// ============================================================

export const createSale = async (saleData, tipo = "online") => {
  const endpoint = tipo === "online" ? "/sales/online" : "/sales/presencial";

  const response = await fetch(`${API_URL}${endpoint}`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(saleData),
  });

  return handleResponse(response);
};

export const getMyPurchases = async () => {
  const response = await fetch(`${API_URL}/sales/my-purchases`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

export const getAllSales = async (params = {}) => {
  const queryParams = new URLSearchParams();

  if (params.tipo) queryParams.append("tipo", params.tipo);
  if (params.skip) queryParams.append("skip", params.skip);
  if (params.limit) queryParams.append("limit", params.limit);

  const response = await fetch(`${API_URL}/sales/all?${queryParams}`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

export const getSaleById = async (id) => {
  const response = await fetch(`${API_URL}/sales/${id}`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

export const cancelSale = async (id) => {
  const response = await fetch(`${API_URL}/sales/${id}/cancel`, {
    method: "POST",
    headers: getHeaders(),
  });

  return handleResponse(response);
};

// ============================================================
// COMPRAS (ADMIN)
// ============================================================

export const createPurchase = async (purchaseData) => {
  const response = await fetch(`${API_URL}/purchases/`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(purchaseData),
  });

  return handleResponse(response);
};

export const getAllPurchases = async () => {
  const response = await fetch(`${API_URL}/purchases/`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

// ============================================================
// ADMIN
// ============================================================

export const createEmployee = async (employeeData) => {
  const response = await fetch(`${API_URL}/admin/employees`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(employeeData),
  });

  return handleResponse(response);
};

export const getAllEmployees = async () => {
  const response = await fetch(`${API_URL}/admin/employees`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

export const getDashboardStats = async () => {
  const response = await fetch(`${API_URL}/admin/dashboard-stats`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

// ============================================================
// SISTEMA EXPERTO
// ============================================================

export const getRecommendations = async (limit = 5) => {
  const response = await fetch(
    `${API_URL}/expert/recommendations?limit=${limit}`,
    {
      headers: getHeaders(),
    },
  );

  return handleResponse(response);
};

export const getInventoryAlerts = async () => {
  const response = await fetch(`${API_URL}/expert/inventory-alerts`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

export const getPromotionSuggestions = async () => {
  const response = await fetch(`${API_URL}/expert/promotion-suggestions`, {
    headers: getHeaders(),
  });

  return handleResponse(response);
};

export const getSalesAnalysis = async (days = 30) => {
  const response = await fetch(
    `${API_URL}/expert/sales-analysis?days=${days}`,
    {
      headers: getHeaders(),
    },
  );

  return handleResponse(response);
};

export default {
  login,
  registerClient,
  getCurrentUser,
  getBooks,
  getBookById,
  getCategories,
  getBestsellers,
  getInventory,
  createBook,
  updateBook,
  deleteBook,
  createSale,
  getMyPurchases,
  getAllSales,
  getSaleById,
  cancelSale,
  createPurchase,
  getAllPurchases,
  createEmployee,
  getAllEmployees,
  getDashboardStats,
  getRecommendations,
  getInventoryAlerts,
  getPromotionSuggestions,
  getSalesAnalysis,
};

// ============================================================
// RESEÑAS
// ============================================================

export const getBookReviews = async (libroId) => {
  const r = await fetch(`${API_URL}/reviews/book/${libroId}`, { headers: getHeaders(false) });
  return handleResponse(r);
};

export const getBookRatingSummary = async (libroId) => {
  const r = await fetch(`${API_URL}/reviews/book/${libroId}/summary`, { headers: getHeaders(false) });
  return handleResponse(r);
};

export const canReview = async (libroId) => {
  const r = await fetch(`${API_URL}/reviews/can-review/${libroId}`, { headers: getHeaders() });
  return handleResponse(r);
};

export const getMyReviews = async () => {
  const r = await fetch(`${API_URL}/reviews/my`, { headers: getHeaders() });
  return handleResponse(r);
};

export const createReview = async (data) => {
  const r = await fetch(`${API_URL}/reviews/`, {
    method: "POST", headers: getHeaders(), body: JSON.stringify(data),
  });
  return handleResponse(r);
};

export const updateReview = async (id, data) => {
  const r = await fetch(`${API_URL}/reviews/${id}`, {
    method: "PUT", headers: getHeaders(), body: JSON.stringify(data),
  });
  return handleResponse(r);
};

export const deleteReview = async (id) => {
  const r = await fetch(`${API_URL}/reviews/${id}`, { method: "DELETE", headers: getHeaders() });
  if (!r.ok) { const d = await r.json(); throw new Error(d.detail); }
  return true;
};

// ============================================================
// REPORTES CSV
// ============================================================

export const exportReport = async (type) => {
  const token = getToken();
  const r = await fetch(`${API_URL}/reports/${type}/export`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Error al exportar");
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `${type}.csv`; a.click();
  URL.revokeObjectURL(url);
};

// ============================================================
// AUDITORÍA
// ============================================================

export const getAuditLogs = async (params = {}) => {
  const q = new URLSearchParams();
  if (params.accion) q.append("accion", params.accion);
  if (params.tabla)  q.append("tabla",  params.tabla);
  if (params.limit)  q.append("limit",  params.limit);
  if (params.skip)   q.append("skip",   params.skip);
  const r = await fetch(`${API_URL}/audit/logs?${q}`, { headers: getHeaders() });
  return handleResponse(r);
};

// ============================================================
// ISBN EXTERNO
// ============================================================

export const lookupISBN = async (isbn) => {
  const r = await fetch(`${API_URL}/isbn/${isbn}`, { headers: getHeaders(false) });
  return handleResponse(r);
};

// ============================================================
// GRÁFICAS
// ============================================================

export const getSalesByMonth = async (months = 6) => {
  const r = await fetch(`${API_URL}/admin/sales-by-month?months=${months}`, { headers: getHeaders() });
  return handleResponse(r);
};
