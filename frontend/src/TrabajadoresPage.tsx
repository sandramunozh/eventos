import { FormEvent, useState } from 'react'
import { Search, Users, UserRound, HeartHandshake, TicketPercent } from 'lucide-react'

type Miembro = { TIPO?: string | null; CUCOD?: number | null; CUNUMID?: string | null; NOMBRE?: string | null }
type Registro = {
  registro: number; fecha: string; tipo_venta?: string | null; valor_tar?: number | null
  valor_des?: number | null; porcentaje?: number | null; categoria?: string | null
  grupo?: number | null; voucher?: string | null; mismo_dia: boolean
}
type TrabajadorFila = {
  TIPO?: string | null
  NOMBRE?: string | null; CUNUMID?: string | null; CUCOD?: number | null; CATTRAB?: string | null
  SUCURSAL?: number | null; TRTIPCONTR?: string | null; EMCODEMPRE?: number | null
  ESTADO_PAGO?: string | null; CUCLASIFIC?: string | null; EMPORCAJA?: string | null
  CUFECNACI?: string | null; TRCODTRABA?: string | null
}
type ConsultaTrabajador = {
  documento: string; fecha: string; encontrado: boolean; tipo_registro: string; cumple_condiciones: boolean
  trabajador: TrabajadorFila | null; trabajador_asociado?: TrabajadorFila | null; condiciones: unknown[]
  grupo_familiar: Miembro[]; beneficiarios: Miembro[]
  subsidios: { mismo_dia: { P: number; R: number }; mismo_mes: { P: number; R: number }; registros: Registro[] }
}

function hoyISO(): string {
  return new Date().toISOString().slice(0, 10)
}

function TablaMiembros({ miembros }: { miembros: Miembro[] }) {
  return <div className="table-wrap">
    <table className="data-table">
      <thead><tr><th>Tipo</th><th>CUCOD</th><th>Documento</th><th>Nombre</th></tr></thead>
      <tbody>
        {miembros.map((m, i) => <tr key={`${m.CUCOD}-${i}`}>
          <td>{m.TIPO || '—'}</td><td>{m.CUCOD ?? '—'}</td><td>{m.CUNUMID || '—'}</td><td>{m.NOMBRE || '—'}</td>
        </tr>)}
      </tbody>
    </table>
  </div>
}

export default function TrabajadoresPage({ api }: {
  api: (path: string, init?: RequestInit) => Promise<unknown>
}) {
  const [documento, setDocumento] = useState('')
  const [fecha, setFecha] = useState(hoyISO())
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const [resultado, setResultado] = useState<ConsultaTrabajador | null>(null)

  async function consultar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const doc = documento.trim()
    if (!doc) { setError('Ingrese el número de documento.'); return }
    setCargando(true); setError(''); setResultado(null)
    try {
      const qs = new URLSearchParams({ documento: doc, ...(fecha ? { fecha } : {}) })
      const res = await api(`/trabajadores?${qs.toString()}`) as ConsultaTrabajador
      setResultado(res)
      if (res.encontrado) setDocumento('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible consultar el trabajador')
    } finally { setCargando(false) }
  }

  const t = resultado?.trabajador
  const esBeneficiario = resultado?.tipo_registro === 'B'
  const asociado = resultado?.trabajador_asociado

  return <>
    <div className="page-heading">
      <div>
        <p className="eyebrow">GESTIÓN COMERCIAL</p>
        <h1>Consulta de trabajadores</h1>
        <p className="muted">Categoría, condiciones, grupo familiar y subsidios otorgados (BDMUF).</p>
      </div>
    </div>

    {error && <p className="error" role="alert">{error}</p>}

    <section className="panel">
      <h2>Consultar por número de documento</h2>
      <p className="muted">La fecha se usa para validar subsidios del mismo día y del mismo mes (por defecto hoy).</p>
      <form className="lookup-form" onSubmit={consultar}>
        <input
          value={documento}
          onChange={(e) => setDocumento(e.target.value)}
          placeholder="Número de documento (ej.: 42154038)"
          aria-label="Número de documento"
          minLength={4}
          maxLength={20}
        />
        <input
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
          aria-label="Fecha de validación"
        />
        <button className="primary" type="submit" disabled={cargando}>
          <Search size={16}/>{cargando ? 'Consultando…' : 'Consultar'}
        </button>
      </form>
    </section>

    {resultado && !resultado.encontrado && (
      <section className="panel">
        <div className="empty"><Users size={28}/><strong>No se encontró ningún registro</strong><span>No existe un registro de trabajador (TIPO='T') ni de beneficiario (TIPO='B') con el documento {resultado.documento} en BDMUF.</span></div>
      </section>
    )}

    {resultado && resultado.encontrado && t && <>
      <section className="panel">
        <div className="panel-heading">
          <div><h2><UserRound size={18}/> {esBeneficiario ? 'Datos del beneficiario' : 'Datos del trabajador'}</h2></div>
          {esBeneficiario
            ? <span className="badge">Beneficiario</span>
            : <span className={`badge ${resultado.cumple_condiciones ? '' : 'badge-alerta'}`}>
                {resultado.cumple_condiciones ? 'Cumple condiciones para subsidio' : 'No cumple condiciones'}
              </span>}
        </div>
        <div className="lookup-result">
          <div className="lookup-field"><small>Nombre</small><strong>{t.NOMBRE || '—'}</strong></div>
          <div className="lookup-field"><small>Documento</small><strong>{t.CUNUMID || '—'}</strong></div>
          <div className="lookup-field"><small>CUCOD</small><strong>{t.CUCOD ?? '—'}</strong></div>
          <div className="lookup-field"><small>Tipo de registro</small><strong>{t.TIPO || resultado.tipo_registro}</strong></div>
          <div className="lookup-field"><small>Categoría</small><strong>{t.CATTRAB || '—'}</strong></div>
          <div className="lookup-field"><small>Tipo contrato (TRTIPCONTR)</small><strong>{t.TRTIPCONTR || '—'}</strong></div>
          <div className="lookup-field"><small>Empresa (EMCODEMPRE)</small><strong>{t.EMCODEMPRE ?? '—'}</strong></div>
          <div className="lookup-field"><small>Estado de pago</small><strong>{t.ESTADO_PAGO || '—'}</strong></div>
          <div className="lookup-field"><small>Clasificación</small><strong>{t.CUCLASIFIC || '(vacio)'}</strong></div>
          {esBeneficiario && (
            <div className="lookup-field"><small>Trabajador asociado</small><strong>{asociado ? `${asociado.NOMBRE} · ${asociado.CUNUMID}` : '—'}</strong></div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2><Users size={18}/> Grupo familiar {esBeneficiario ? '(del trabajador asociado)' : '(trabajadores)'}</h2>
            <p className="muted">Consulta 2: filas con CUCODTRABAJADOR = {esBeneficiario ? asociado?.CUCOD : t.CUCOD}.</p>
          </div>
        </div>
        {resultado.grupo_familiar.length === 0
          ? <p className="muted">Sin beneficiarios registrados para este trabajador.</p>
          : <TablaMiembros miembros={resultado.grupo_familiar}/>}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div><h2><HeartHandshake size={18}/> Grupo familiar (beneficiarios)</h2><p className="muted">Consulta 3: titular + beneficiarios en VIAFILIADOSFACTURACION.</p></div>
        </div>
        {resultado.beneficiarios.length === 0
          ? <p className="muted">Sin registros.</p>
          : <TablaMiembros miembros={resultado.beneficiarios}/>}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div><h2><TicketPercent size={18}/> Subsidios otorgados</h2><p className="muted">Validación del {resultado.fecha} · tipos de venta P y R por separado.</p></div>
        </div>
        <div className="lookup-result">
          <div className="lookup-field"><small>Mismo día · P</small><strong>{resultado.subsidios.mismo_dia.P}</strong></div>
          <div className="lookup-field"><small>Mismo día · R</small><strong>{resultado.subsidios.mismo_dia.R}</strong></div>
          <div className="lookup-field"><small>Mismo mes · P</small><strong>{resultado.subsidios.mismo_mes.P}</strong></div>
          <div className="lookup-field"><small>Mismo mes · R</small><strong>{resultado.subsidios.mismo_mes.R}</strong></div>
        </div>
        {resultado.subsidios.registros.length === 0
          ? <p className="muted" style={{marginTop: '.8rem'}}>Sin subsidios otorgados en el mes de la fecha consultada.</p>
          : <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>Registro</th><th>Fecha</th><th>Tipo venta</th><th>Valor tarifa</th><th>Valor descuento</th><th>%</th><th>Categoría</th><th>Voucher</th><th>Mismo día</th></tr></thead>
                <tbody>
                  {resultado.subsidios.registros.map((r) => <tr key={r.registro}>
                    <td>{r.registro}</td><td>{r.fecha}</td><td>{r.tipo_venta || '—'}</td>
                    <td>{r.valor_tar ?? '—'}</td><td>{r.valor_des ?? '—'}</td><td>{r.porcentaje ?? '—'}</td>
                    <td>{r.categoria || '—'}</td><td>{r.voucher || '—'}</td>
                    <td>{r.mismo_dia ? <span className="badge">Sí</span> : <span className="badge badge-vacio">No</span>}</td>
                  </tr>)}
                </tbody>
              </table>
            </div>}
      </section>
    </>}

    <p className="fine-print">Datos de BDMUF: VIAFILIADOSFACTURACIONDATAFONOV, VIAFILIADOSFACTURACION, TBSUBESP y TBSUBESPDET.</p>
  </>
}
