#!/usr/bin/env python3
"""
Termômetro ConstruExpert (metodologia oficial v1.0, a mesma da edição mensal do dia 15)

T = soma dos pilares ponderados. Cada indicador vira S de 0 a 100 contra o mínimo e o
máximo dos últimos 60 meses (menor é melhor: 100 * (max - x) / (max - min)).
Pilar = média dos indicadores dele. Faixas: 0-39 vermelho, 40-59 amarelo, 60-100 verde.
Pilar sem nenhum dado fica de fora e os pesos dos demais são reescalados (a página avisa).

Uso:
  python coleta_ce.py                     # busca tudo nas APIs (GitHub Actions)
  python coleta_ce.py --fixtures pasta/   # testes com arquivos salvos

Automático (sem chave):
  Banco Central SGS 432     Selic meta                                   (Crédito, menor é melhor)
  Banco Central SGS 7456    INCC-M mensal -> acumulado em 12 meses       (Custo, menor é melhor)
  Ipeadata FGV12_ICSTCA12   ICST, Índice de Confiança da Construção      (Confiança, maior é melhor)
  IBGE SIDRA 8883           Varejo de material de construção (PMC)       (Atividade, maior é melhor)
  IBGE SIDRA 2296           SINAPI: custo do m² por estado (só exibição)
Manual (manual.json, séries mensais; vazio = ainda sem dado):
  cub_rs, cub_sc (Custo) · sbpe (Crédito) · cimento (Atividade) · caged (Emprego)
"""
import argparse, json, os, sys, urllib.request
from datetime import date, datetime, timezone

UA = {"User-Agent": "termometro-construexpert/1.0"}
AQUI = os.path.dirname(os.path.abspath(__file__))

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

PILARES = [
    {"id": "custo", "nome": "Custo", "peso": 25, "explica": "Quanto ficou mais caro construir. Menos alta é melhor."},
    {"id": "confianca", "nome": "Confiança", "peso": 25, "explica": "O humor dos empresários da construção."},
    {"id": "credito", "nome": "Crédito", "peso": 20, "explica": "Custo e oferta de dinheiro para obra e para o comprador."},
    {"id": "atividade", "nome": "Atividade", "peso": 15, "explica": "Demanda real: material vendido e cimento consumido."},
    {"id": "emprego", "nome": "Emprego", "peso": 15, "explica": "Vagas com carteira abertas pelo setor."},
]

INDICADORES = [
    {"id": "incc", "pilar": "custo", "nome": "INCC-M em 12 meses", "un": "%", "menor_melhor": True, "fonte": "FGV IBRE via Banco Central (SGS 7456)", "auto": True},
    {"id": "cub_rs", "pilar": "custo", "nome": "CUB/m² RS em 12 meses", "un": "%", "menor_melhor": True, "fonte": "Sinduscon-RS", "auto": False},
    {"id": "cub_sc", "pilar": "custo", "nome": "CUB/m² SC em 12 meses", "un": "%", "menor_melhor": True, "fonte": "Sinduscon-SC", "auto": False},
    {"id": "icst", "pilar": "confianca", "nome": "ICST, confiança da construção", "un": "pts", "menor_melhor": False, "fonte": "FGV IBRE via Ipeadata", "auto": True},
    {"id": "selic", "pilar": "credito", "nome": "Selic", "un": "% a.a.", "menor_melhor": True, "fonte": "Banco Central (SGS 432)", "auto": True},
    {"id": "sbpe", "pilar": "credito", "nome": "Financiamento SBPE em 12 meses", "un": "%", "menor_melhor": False, "fonte": "Abecip", "auto": False},
    {"id": "varejo", "pilar": "atividade", "nome": "Varejo de material de construção", "un": "%", "menor_melhor": False, "fonte": "IBGE, PMC (SIDRA 8883)", "auto": True},
    {"id": "cimento", "pilar": "atividade", "nome": "Vendas de cimento em 12 meses", "un": "%", "menor_melhor": False, "fonte": "SNIC", "auto": False},
    {"id": "caged", "pilar": "emprego", "nome": "Caged da construção, saldo em 12 meses", "un": "vagas", "menor_melhor": False, "fonte": "Novo Caged (MTE)", "auto": False},
]

URL_VAREJO = "https://apisidra.ibge.gov.br/values/t/8883/n1/all/v/11709/p/all/c11046/56736/c85/2762"
URL_ICST = "http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='FGV12_ICSTCA12')"
URL_SINAPI = "https://apisidra.ibge.gov.br/values/t/2296/n1/all/n3/all/v/48,1198/p/last%201"  # 48 custo do m² (R$), 1198 variação em 12 meses

def fx_or(fx, nome, url):
    return json.load(open(os.path.join(fx, nome), encoding="utf-8")) if fx else get(url)

def sgs(serie, fx=None):
    """O BC aceita no máximo 10 anos por consulta em séries diárias: busca em janelas de 8 anos."""
    if fx: return json.load(open(os.path.join(fx, f"sgs_{serie}.json"), encoding="utf-8"))
    hoje, ini, linhas = date.today(), date(2008, 1, 1), []
    while ini <= hoje:
        fim = min(date(ini.year + 8, 12, 31), hoje)
        linhas += get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json"
                      f"&dataInicial={ini:%d/%m/%Y}&dataFinal={fim:%d/%m/%Y}")
        ini = date(fim.year + 1, 1, 1)
    return linhas

def mensal_sgs(rows):
    out = {}
    for r in rows:
        try: out[datetime.strptime(r["data"], "%d/%m/%Y").strftime("%Y-%m")] = float(r["valor"])
        except (KeyError, ValueError, TypeError): pass
    return dict(sorted(out.items()))

def mensal_ipea(j):
    out = {}
    for r in j.get("value", []):
        if r.get("VALVALOR") is None: continue
        out[r["VALDATA"][:7]] = float(r["VALVALOR"])
    return dict(sorted(out.items()))

def dims_sidra(cab):
    d = {}
    for k in range(1, 9):
        rot = cab.get(f"D{k}N", "")
        if not rot: continue
        if rot.startswith("Variável"): d["var"] = k
        elif rot.startswith("Mês"): d["mes"] = k
        elif "Unidade da Federação" in rot or rot.startswith("Brasil"): d.setdefault("terr", k)
    return d

def mensal_sidra(rows):
    out = {}
    if not rows or len(rows) < 2: return out
    d = dims_sidra(rows[0])
    for r in rows[1:]:
        try: v = float(r["V"])
        except (ValueError, KeyError): continue
        c = r.get(f"D{d.get('mes', 0)}C", "")
        if len(c) == 6: out[f"{c[:4]}-{c[4:]}"] = v
    return dict(sorted(out.items()))

def acum12(var):
    out, ms = {}, sorted(var)
    for i in range(11, len(ms)):
        f = 1.0
        for m in ms[i-11:i+1]: f *= 1 + var[m] / 100
        out[ms[i]] = round((f - 1) * 100, 2)
    return out

def ler_sinapi(rows):
    if not rows or len(rows) < 2: return None
    d = dims_sidra(rows[0])
    if len(d) < 3: return None
    lugares, ref = {}, None
    for r in rows[1:]:
        try: v = float(r["V"])
        except (ValueError, KeyError): continue
        terr = r[f"D{d['terr']}N"]; var = r[f"D{d['var']}C"]; ref = r[f"D{d['mes']}C"]
        l = lugares.setdefault(terr, {"nome": terr})
        if var == "48": l["custo"] = round(v, 2)
        elif var == "1198": l["var12"] = round(v, 2)
    siglas = {"Acre":"AC","Alagoas":"AL","Amapá":"AP","Amazonas":"AM","Bahia":"BA","Ceará":"CE","Distrito Federal":"DF",
              "Espírito Santo":"ES","Goiás":"GO","Maranhão":"MA","Mato Grosso":"MT","Mato Grosso do Sul":"MS","Minas Gerais":"MG",
              "Pará":"PA","Paraíba":"PB","Paraná":"PR","Pernambuco":"PE","Piauí":"PI","Rio de Janeiro":"RJ","Rio Grande do Norte":"RN",
              "Rio Grande do Sul":"RS","Rondônia":"RO","Roraima":"RR","Santa Catarina":"SC","São Paulo":"SP","Sergipe":"SE","Tocantins":"TO"}
    brasil = lugares.pop("Brasil", None)
    ufs = sorted([dict(l, uf=siglas.get(l["nome"], l["nome"][:2].upper())) for l in lugares.values() if "custo" in l], key=lambda x: -x["custo"])
    return {"ref": f"{ref[:4]}-{ref[4:6]}" if ref and len(ref) == 6 else ref, "brasil": brasil, "ufs": ufs}

# ---------------------------------------------------------------- cálculo
def meses_ate(m, n):
    a, mm = int(m[:4]), int(m[5:7]); out = []
    for _ in range(n):
        out.append(f"{a:04d}-{mm:02d}"); mm -= 1
        if mm == 0: mm = 12; a -= 1
    return out

def pontuar(serie, ind, ate=None):
    """S de 0 a 100 da última leitura até 'ate' contra a janela de 60 meses que termina nela."""
    ms = [m for m in serie if ate is None or m <= ate]
    if not ms: return None
    m = max(ms); x = serie[m]
    jan = [serie[k] for k in meses_ate(m, 60) if k in serie]
    if len(jan) < 12: return None
    lo, hi = min(jan), max(jan)
    if hi == lo: s = 50.0
    else: s = 100 * ((hi - x) if ind["menor_melhor"] else (x - lo)) / (hi - lo)
    return {"mes": m, "valor": x, "s": round(s, 1), "min": lo, "max": hi, "n": len(jan)}

def termometro(series, ate=None):
    pil = []
    for p in PILARES:
        its = [pontuar(series[i["id"]], i, ate) for i in INDICADORES if i["pilar"] == p["id"] and series.get(i["id"])]
        its = [x for x in its if x]
        pil.append(sum(x["s"] for x in its) / len(its) if its else None)
    pesos = [p["peso"] for p, v in zip(PILARES, pil) if v is not None]
    if not pesos: return None, pil
    t = sum(p["peso"] * v for p, v in zip(PILARES, pil) if v is not None) / sum(pesos)
    return round(t, 1), pil

def faixa(t):
    return "Vermelho" if t < 40 else ("Amarelo" if t < 60 else "Verde")

def calcular(fx=None, manual=None):
    avisos = []
    def tenta(nome, fn, padrao):
        try: return fn()
        except Exception as e:
            avisos.append(f"{nome}: {e}"); print(f"aviso: {nome} falhou: {e}", file=sys.stderr); return padrao
    series = {
        "selic": tenta("selic", lambda: mensal_sgs(sgs(432, fx)), {}),
        "incc": tenta("incc", lambda: acum12(mensal_sgs(sgs(7456, fx))), {}),
        "icst": tenta("icst", lambda: mensal_ipea(fx_or(fx, "ipea_icst.json", URL_ICST)), {}),
        "varejo": tenta("varejo", lambda: mensal_sidra(fx_or(fx, "sidra_8883.json", URL_VAREJO)), {}),
    }
    manual = manual or {}
    for i in INDICADORES:
        if not i["auto"]:
            series[i["id"]] = {k: float(v) for k, v in (manual.get(i["id"]) or {}).items() if v is not None}
    sinapi = tenta("sinapi", lambda: ler_sinapi(fx_or(fx, "sidra_2296.json", URL_SINAPI)), None)
    return montar(series, sinapi, avisos)

def montar(series, sinapi=None, avisos=None):
    avisos = avisos or []
    t, pil = termometro(series)
    indicadores = []
    for i in INDICADORES:
        sc = pontuar(series.get(i["id"], {}), i)
        indicadores.append({k: i[k] for k in ("id", "pilar", "nome", "un", "menor_melhor", "fonte", "auto")} | (sc or {}) | {"tem": bool(sc)})
    pilares = [p | {"pontos": None if v is None else round(v, 1)} for p, v in zip(PILARES, pil)]

    # Histórico mensal de T desde 2016 (cada mês com a leitura disponível até ele)
    todos = sorted({m for s in series.values() for m in s if m >= "2016-01"})
    hist = []
    for m in todos:
        tm, _ = termometro(series, ate=m)
        if tm is not None: hist.append([m, tm])
    ref = max((x["mes"] for x in indicadores if x["tem"]), default=None)
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "metodologia": "v1.0",
        "termometro": t, "faixa": faixa(t) if t is not None else None, "mes_ref": ref,
        "pilares": pilares, "indicadores": indicadores,
        "historico": hist, "sinapi": sinapi, "avisos": avisos,
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures"); ap.add_argument("--manual", default=os.path.join(AQUI, "manual.json"))
    ap.add_argument("--saida", default="dados.json")
    a = ap.parse_args()
    manual = json.load(open(a.manual, encoding="utf-8")) if os.path.exists(a.manual) else {}
    d = calcular(a.fixtures, manual)
    if d["termometro"] is None:
        sys.exit("nenhum pilar com dados; dados.json anterior mantido")
    with open(a.saida, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    print(f"ok: Termômetro {d['termometro']} ({d['faixa']}) · {len(d['historico'])} meses · avisos: {len(d['avisos'])}")
