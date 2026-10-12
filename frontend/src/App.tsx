import { FormEvent, useEffect, useState } from 'react'
import { CalendarDays, LogOut, PlusCircle, RefreshCw, ShieldCheck } from 'lucide-react'

const API = import.meta.env.VITE_API_BASE_URL || '/api/v1'
type User = { id: number; username: string; role: string }
type Solicitud = {
  id: number; numero: string; cliente_nombre: string; nombre_evento: string;
  fecha_inicio: string; fecha_fin: string; asistentes_estimados: number; estado: string
}

export default function App() {
  const [token, setToken] = useState(sessionStorage.getItem('token') || '')
  const [user, setUser] = useState<User | null>(null)
  const [error, setError] = useState('')
  const [items, setItems] = useState<Solicitud[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)

  async function api(path: string, init: RequestInit = {}) {
    const response = await fetch(`${API}${path}`, {
      ...init,
      headers: { ...(init.headers || {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail || `Error HTTP ${response.status}`)
    }
    return response.status === 204 ? null : response.json()
  }

  async function login(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError('')
    const data = new FormData(e.currentTarget)
    const body = new URLSearchParams()
    body.set('username', String(data.get('username') || ''))
    body.set('password', String(data.get('password') || ''))
    try {
      const response = await fetch(`${API}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'No fue posible iniciar sesión')
      sessionStorage.setItem('token', result.access_token)
      setToken(result.access_token); setUser(result.user)
    } catch (err) { setError(err instanceof Error ? err.message : 'Error de conexión') }
  }

  async function refresh() {
    if (!token) return
    setLoading(true); setError('')
    try {
      const me = await api('/auth/me')
      setUser(me)
      setItems(await api('/solicitudes'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error de conexión')
      sessionStorage.removeItem('token'); setToken(''); setUser(null)
    } finally { setLoading(false) }
  }

  useEffect(() => { if (token) void refresh() }, [token])

  async function createSolicitud(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError('')
    const form = e.currentTarget
    const data = new FormData(form)
    const payload = Object.fromEntries(data.entries())
    try {
      await api('/solicitudes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...payload, asistentes_estimados: Number(payload.asistentes_estimados) }) })
      setShowForm(false); form.reset(); await refresh()
    } catch (err) { setError(err instanceof Error ? err.message : 'No fue posible guardar la solicitud') }
  }

  function logout() {
    sessionStorage.removeItem('token'); setToken(''); setUser(null); setItems([])
  }

  if (!token || !user) return <main className="login-shell">
    <section className="login-card">
      <div className="brand-mark"><CalendarDays size={28} /></div>
      <p className="eyebrow">PARQUE CONSOTÁ · COMFAMILIAR</p>
      <h1>Gestión de eventos</h1>
      <p className="muted">Ingresa con tu cuenta autorizada para continuar.</p>
      <form onSubmit={login} className="stack">
        <label>Usuario<input name="username" autoComplete="username" required minLength={3} /></label>
        <label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" type="submit"><ShieldCheck size={18}/> Iniciar sesión</button>
      </form>
      <p className="fine-print">Acceso exclusivo para usuarios autorizados.</p>
    </section>
  </main>

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand-inline"><span className="brand-mark small"><CalendarDays size={20}/></span><div><strong>Gestión de eventos</strong><small>Parque Consotá</small></div></div>
      <div className="user-actions"><span>{user.username} · {user.role}</span><button className="icon-button" onClick={logout} aria-label="Cerrar sesión"><LogOut size={18}/><span>Salir</span></button></div>
    </header>
    <main className="content">
      <div className="page-heading"><div><p className="eyebrow">OPERACIÓN INSTITUCIONAL</p><h1>Solicitudes de eventos</h1><p className="muted">Registra y consulta las solicitudes recibidas.</p></div><button className="primary" onClick={() => setShowForm(!showForm)}><PlusCircle size={18}/>{showForm ? 'Cerrar formulario' : 'Nueva solicitud'}</button></div>
      {error && <p className="error" role="alert">{error}</p>}
      {showForm && <section className="panel"><h2>Nueva solicitud</h2><form className="form-grid" onSubmit={createSolicitud}>
        <label>Empresa o cliente<input name="cliente_nombre" required minLength={2}/></label>
        <label>NIT o documento (opcional)<input name="documento_cliente" maxLength={40}/></label>
        <label>Nombre del contacto<input name="contacto_nombre" required minLength={2}/></label>
        <label>Correo electrónico<input name="correo" type="email" required/></label>
        <label>Teléfono<input name="telefono" type="tel" required minLength={7}/></label>
        <label>Nombre del evento<input name="nombre_evento" required minLength={3}/></label>
        <label>Fecha de inicio<input name="fecha_inicio" type="date" required/></label>
        <label>Fecha de finalización<input name="fecha_fin" type="date" required/></label>
        <label>Asistentes estimados<input name="asistentes_estimados" type="number" min="1" max="100000" required/></label>
        <label className="full">Descripción y servicios solicitados<textarea name="descripcion" rows={3} required minLength={5}/></label>
        <div className="full form-actions"><button type="button" className="secondary" onClick={() => setShowForm(false)}>Cancelar</button><button type="submit" className="primary">Guardar solicitud</button></div>
      </form></section>}
      <section className="panel">
        <div className="panel-heading"><div><h2>Solicitudes registradas</h2><p className="muted">{items.length} registro(s) recientes</p></div><button className="secondary" onClick={() => void refresh()} disabled={loading}><RefreshCw size={16}/>{loading ? 'Actualizando…' : 'Actualizar'}</button></div>
        {items.length === 0 ? <div className="empty"><CalendarDays size={28}/><strong>No hay solicitudes para mostrar</strong><span>Registra una nueva solicitud para iniciar.</span></div> :
          <div className="cards">{items.map(item => <article className="request-card" key={item.id}><div className="request-top"><span className="request-number">{item.numero}</span><span className={`status status-${item.estado.toLowerCase()}`}>{item.estado.replaceAll('_',' ')}</span></div><h3>{item.nombre_evento}</h3><p>{item.cliente_nombre}</p><div className="request-meta"><span><CalendarDays size={15}/>{item.fecha_inicio} – {item.fecha_fin}</span><span>{item.asistentes_estimados} asistentes</span></div></article>)}</div>}
      </section>
      <p className="fine-print">Versión inicial · Las aprobaciones y rutas administrativas se incorporarán en las siguientes fases.</p>
    </main>
  </div>
}
