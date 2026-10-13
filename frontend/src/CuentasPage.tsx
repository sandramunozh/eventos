import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Search, Filter, RefreshCw, Users, ChevronLeft, ChevronRight, BadgeCheck, XCircle } from 'lucide-react'

type Cuenta = {
  id: number
  cu_cod: number | null
  cu_num_id: string
  cu_pri_nom: string | null
  cu_seg_nom: string | null
  cu_pri_ape: string | null
  cu_seg_ape: string | null
  identificacion: string | null
  tercero: string | null
  nom_tercero: string | null
  consultado_en: string
}

type PaginaCuentas = { items: Cuenta[]; total: number; page: number; page_size: number; pages: number }

type TerceroData = {
  cuCod: number
  cuNumId: string
  cuPriNom: string
  cuSegNom: string | null
  cuPriApe: string
  cuSegApe: string | null
  identificacion: string
  tercero: string
  nomTercero: string
}

type LookupResult = { result: number; message: string; data: TerceroData | null }

const VACIO = { numero_identificacion: '', nombre: '', codigo: '', tercero: '', nom_tercero: '' }

function nombreCompleto(c: Cuenta): string {
  return [c.cu_pri_nom, c.cu_seg_nom, c.cu_pri_ape, c.cu_seg_ape].filter(Boolean).join(' ') || '—'
}

function fechaCorta(iso: string): string {
  return iso ? iso.replace('T', ' ').slice(0, 16) : ''
}

export default function CuentasPage({ api }: {
  api: (path: string, init?: RequestInit) => Promise<unknown>
}) {
  const [data, setData] = useState<PaginaCuentas>({ items: [], total: 0, page: 1, page_size: 20, pages: 0 })
  const [filtros, setFiltros] = useState({ ...VACIO })
  const [aplicados, setAplicados] = useState({ ...VACIO })
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [ident, setIdent] = useState('')
  const [lookup, setLookup] = useState<LookupResult | null>(null)
  const [lookupLoading, setLookupLoading] = useState(false)

  const cargar = useCallback(async (p = 1, tam = 20, f = VACIO) => {
    setLoading(true); setError('')
    try {
      const qs = new URLSearchParams({ page: String(p), page_size: String(tam) })
      Object.entries(f).forEach(([k, v]) => { if (v) qs.set(k, v) })
      const resultado = await api(`/cuentas?${qs.toString()}`) as PaginaCuentas
      setData(resultado); setPage(p)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error de conexión')
    } finally { setLoading(false) }
  }, [api])

  useEffect(() => { void cargar(1, 20) }, [cargar])

  function aplicarFiltros(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setAplicados({ ...filtros })
    void cargar(1, pageSize, filtros)
  }

  function limpiarFiltros() {
    setFiltros({ ...VACIO }); setAplicados({ ...VACIO })
    void cargar(1, pageSize, VACIO)
  }

  async function consultarTercero(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const num = ident.trim()
    if (!num) {
      setLookup({ result: -2, message: 'El número de identificación es requerido.', data: null })
      return
    }
    setLookupLoading(true); setLookup(null); setError('')
    try {
      const res = await api(`/cuentas/tercero/${encodeURIComponent(num)}`) as LookupResult
      setLookup(res)
      if (res.result === 1) {
        setIdent('')
        await cargar(page, pageSize, aplicados)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible consultar el tercero')
    } finally { setLookupLoading(false) }
  }

  function cambiarTam(nuevo: number) {
    setPageSize(nuevo)
    void cargar(1, nuevo, aplicados)
  }

  const desde = data.total === 0 ? 0 : (data.page - 1) * data.page_size + 1
  const hasta = Math.min(data.page * data.page_size, data.total)

  return <>
    <div className="page-heading">
      <div>
        <p className="eyebrow">GESTIÓN COMERCIAL</p>
        <h1>Cuentas</h1>
        <p className="muted">Consulta paginada de clientes con datos del tercero en MUF y JDE.</p>
      </div>
      <button className="secondary" onClick={() => void cargar(page, pageSize, aplicados)} disabled={loading}>
        <RefreshCw size={16}/>{loading ? 'Actualizando…' : 'Actualizar'}
      </button>
    </div>

    {error && <p className="error" role="alert">{error}</p>}

    <section className="panel">
      <h2>Consultar tercero por identificación</h2>
      <p className="muted">Ingresa el número sin separadores de miles (ej.: 75084840). El dato se guarda para la consulta listada.</p>
      <form className="lookup-form" onSubmit={consultarTercero}>
        <input
          value={ident}
          onChange={(e) => setIdent(e.target.value)}
          placeholder="Número de identificación"
          aria-label="Número de identificación"
          minLength={4}
          maxLength={20}
        />
        <button className="primary" type="submit" disabled={lookupLoading}>
          <Search size={16}/>{lookupLoading ? 'Consultando…' : 'Consultar'}
        </button>
      </form>
      {lookup && (
        lookup.result === 1 && lookup.data ? (
          <div className="lookup-result">
            <div className="lookup-field"><small>Identificación</small><strong>{lookup.data.cuNumId}</strong></div>
            <div className="lookup-field"><small>Nombre titular</small><strong>{[lookup.data.cuPriNom, lookup.data.cuSegNom, lookup.data.cuPriApe, lookup.data.cuSegApe].filter(Boolean).join(' ')}</strong></div>
            <div className="lookup-field"><small>Cód. cuenta MUF</small><strong>{lookup.data.cuCod}</strong></div>
            <div className="lookup-field"><small>Tercero JDE (ABAN8)</small><strong>{lookup.data.tercero || '—'}</strong></div>
            <div className="lookup-field"><small>Nombre tercero JDE</small><strong>{lookup.data.nomTercero || '—'}</strong></div>
            <div className="lookup-field ok"><BadgeCheck size={16}/> <span>{lookup.message}</span></div>
          </div>
        ) : (
          <p className="lookup-vacio"><XCircle size={16}/> {lookup.message || 'Sin datos.'}</p>
        )
      )}
    </section>

    <section className="panel">
      <div className="panel-heading">
        <div><h2>Clientes consultados</h2><p className="muted">Mostrando {desde} a {hasta} de {data.total} cliente(s) · página {data.page} de {data.pages || 1}</p></div>
      </div>
      <form className="filter-bar" onSubmit={aplicarFiltros}>
        <label>Identificación<input value={filtros.numero_identificacion} onChange={(e) => setFiltros({ ...filtros, numero_identificacion: e.target.value })} placeholder="Ej.: 75084"/></label>
        <label>Nombre<input value={filtros.nombre} onChange={(e) => setFiltros({ ...filtros, nombre: e.target.value })} placeholder="Nombre o apellido"/></label>
        <label>Cód. cuenta MUF<input value={filtros.codigo} onChange={(e) => setFiltros({ ...filtros, codigo: e.target.value })} placeholder="Ej.: 123456"/></label>
        <label>Tercero JDE<input value={filtros.tercero} onChange={(e) => setFiltros({ ...filtros, tercero: e.target.value })} placeholder="Código ABAN8"/></label>
        <label>Nombre tercero JDE<input value={filtros.nom_tercero} onChange={(e) => setFiltros({ ...filtros, nom_tercero: e.target.value })} placeholder="Nombre en JDE"/></label>
        <div className="filter-actions">
          <button className="primary" type="submit"><Filter size={16}/>Filtrar</button>
          <button className="secondary" type="button" onClick={limpiarFiltros}>Limpiar</button>
        </div>
      </form>

      {data.items.length === 0 ? (
        <div className="empty"><Users size={28}/><strong>No hay clientes para mostrar</strong><span>Consulta un tercero por identificación o ajusta los filtros.</span></div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Identificación</th>
                <th>Nombre titular</th>
                <th>Cód. cuenta MUF</th>
                <th>Id. JDE</th>
                <th>Tercero JDE</th>
                <th>Nombre tercero JDE</th>
                <th>Consultado</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c, i) => (
                <tr key={c.id}>
                  <td>{desde + i}</td>
                  <td><strong>{c.cu_num_id}</strong></td>
                  <td>{nombreCompleto(c)}</td>
                  <td>{c.cu_cod ?? '—'}</td>
                  <td>{c.identificacion || <span className="badge badge-vacio">sin JDE</span>}</td>
                  <td>{c.tercero || <span className="badge badge-vacio">sin JDE</span>}</td>
                  <td>{c.nom_tercero || '—'}</td>
                  <td>{fechaCorta(c.consultado_en)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="pagination">
        <span>Mostrando {desde} a {hasta} de {data.total} cliente(s)</span>
        <div className="pager">
          <label className="pager-size">Filas
            <select value={pageSize} onChange={(e) => cambiarTam(Number(e.target.value))}>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </label>
          <button className="secondary" onClick={() => void cargar(data.page - 1, pageSize, aplicados)} disabled={data.page <= 1}><ChevronLeft size={16}/>Anterior</button>
          <button className="secondary" onClick={() => void cargar(data.page + 1, pageSize, aplicados)} disabled={data.page >= (data.pages || 1)}>Siguiente<ChevronRight size={16}/></button>
        </div>
      </div>
    </section>
    <p className="fine-print">Los datos provienen del servicio WebApiComfamiliar (api/Facturacion/Tercero). Los campos JDE se muestran vacíos cuando no hay coincidencia.</p>
  </>
}
