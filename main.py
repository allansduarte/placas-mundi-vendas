import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard Placas Mundi",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #3498db, #2980b9);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .resposta-destaque {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def carregar_dados(uploaded_file):
    """Carrega e processa os dados do CSV da Placas Mundi"""
    try:
        # Ler arquivo enviado pelo usuário
        df = pd.read_csv(uploaded_file)
        
        # Filtrar registros válidos (remover cabeçalhos de mês e valores nulos)
        meses_invalidos = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO']
        df_valid = df[~df['DATA'].isin(meses_invalidos)].copy()
        
        # Remover linhas onde DATA ou UF são nulos/vazios
        df_valid = df_valid.dropna(subset=['DATA', 'UF'])
        df_valid = df_valid[df_valid['DATA'].str.strip() != '']
        df_valid = df_valid[df_valid['UF'].str.strip() != '']
        
        # Calcular quantidade total de plaquetas por venda
        colunas_quantidade = [col for col in df_valid.columns if col.startswith(('6F', '8F'))]
        df_valid[colunas_quantidade] = df_valid[colunas_quantidade].fillna(0)
        
        # Converter para numérico, forçando erros para 0
        for col in colunas_quantidade:
            df_valid[col] = pd.to_numeric(df_valid[col], errors='coerce').fillna(0)
        
        df_valid['QUANTIDADE_TOTAL'] = df_valid[colunas_quantidade].sum(axis=1)
        
        # Converter data de forma mais robusta
        df_valid['DATA'] = pd.to_datetime(df_valid['DATA'], format='%d/%m/%Y', errors='coerce')
        
        # Remover linhas com datas inválidas
        df_valid = df_valid.dropna(subset=['DATA'])
        
        # Extrair mês e nome do mês
        df_valid['MES'] = df_valid['DATA'].dt.month
        df_valid['MES_NOME'] = df_valid['DATA'].dt.strftime('%b')
        
        return df_valid
        
    except FileNotFoundError:
        st.error("Arquivo CSV não encontrado. Por favor, coloque o arquivo 'Planilha2025PM  Página1.csv' no diretório do script.")
        return None

def criar_mapeamento_regioes():
    """Cria mapeamento de estados para regiões"""
    return {
        'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
        'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
        'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
        'Sul': ['PR', 'RS', 'SC']
    }

def calcular_vendas_por_regiao(df):
    """Calcula vendas por região"""
    regioes_map = criar_mapeamento_regioes()
    
    # Criar mapeamento estado -> região
    estado_para_regiao = {}
    for regiao, estados in regioes_map.items():
        for estado in estados:
            estado_para_regiao[estado] = regiao
    
    # Adicionar coluna de região
    df['REGIAO'] = df['UF'].map(estado_para_regiao)
    
    # Calcular vendas por região
    vendas_regiao = df.groupby('REGIAO').agg({
        'QUANTIDADE_TOTAL': 'sum',
        'CLIENTE': 'nunique',
        'DATA': 'count'
    }).rename(columns={
        'QUANTIDADE_TOTAL': 'Quantidade',
        'CLIENTE': 'Clientes',
        'DATA': 'Vendas'
    }).reset_index()
    
    vendas_regiao['Percentual'] = (vendas_regiao['Quantidade'] / vendas_regiao['Quantidade'].sum() * 100).round(1)
    
    return vendas_regiao.sort_values('Quantidade', ascending=False)

def main():
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard Placas Mundi</h1>
        <h3>Análise de Vendas de Plaquetas - 2025</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload do arquivo CSV
    st.subheader("📁 Upload do Arquivo de Dados")
    
    uploaded_file = st.file_uploader(
        "Escolha o arquivo CSV com os dados de vendas da Placas Mundi",
        type=['csv'],
        help="Faça upload do arquivo 'Planilha2025PM Página1.csv' ou similar"
    )
    
    # Exemplo de formato esperado
    with st.expander("ℹ️ Formato esperado do arquivo"):
        st.write("""
        **Colunas necessárias:**
        - DATA: Data da venda (formato DD/MM/YYYY)
        - UF: Estado (sigla de 2 letras)
        - CLIENTE: Nome do cliente
        - CIDADE: Cidade do cliente
        - 6F, 8F, 6F_1, 8F_1, etc.: Quantidades por modelo
        - CONSULTOR: Nome do consultor
        - STATUS: Status da venda
        
        **Exemplo de linha:**
        ```
        05/01/2025,AM,Norte Conectado,Manaus,Amarelo,8 furos,,2000,...
        ```
        """)
        
        # Gerar arquivo de exemplo para download
        exemplo_csv = """DATA,Cidade,UF,CLIENTE,OBS.:,COR,MODELO,6F,8F,6F_1,8F_1,CONSULTOR,STATUS
05/01/2025,Manaus,AM,Norte Conectado,,Amarelo,8 furos,,2000,,,Rosangela,Finalizada
06/01/2025,Hortolândia,SP,Hixis Telecom,,Verde,6 furos,,,500,,M. Rodrigo,Finalizada
07/01/2025,Belo Horizonte,MG,TechNet,,,6 furos,1500,,,,Ana Silva,Finalizada"""
        
        st.download_button(
            label="📥 Baixar arquivo de exemplo",
            data=exemplo_csv,
            file_name="exemplo_placas_mundi.csv",
            mime="text/csv",
            help="Use este arquivo como modelo para seus dados"
        )
    
    if uploaded_file is None:
        st.info("👆 Por favor, faça upload do arquivo CSV para começar a análise.")
        st.stop()
    
    # Carregar dados do arquivo enviado
    with st.spinner("📊 Processando dados..."):
        df = carregar_dados(uploaded_file)
    if df is None or df.empty:
        st.error("❌ Não foi possível carregar os dados do arquivo CSV.")
        st.info("📋 Possíveis problemas:")
        st.write("1. Arquivo corrompido ou em formato inválido")
        st.write("2. Colunas obrigatórias (DATA, UF) não encontradas")
        st.write("3. Formato de data incorreto (deve ser DD/MM/YYYY)")
        st.write("4. Arquivo vazio ou apenas com cabeçalhos")
        st.stop()
    
    # Verificar se temos dados válidos
    if len(df) == 0:
        st.warning("⚠️ O arquivo foi carregado mas não contém dados válidos.")
        st.stop()
        
    # Mostrar informações do arquivo carregado
    st.success(f"✅ Arquivo carregado com sucesso! {len(df)} registros encontrados.")
    
    # Opção para visualizar dados brutos
    with st.expander("👀 Visualizar dados carregados (primeiras 10 linhas)"):
        st.dataframe(df.head(10))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Linhas", len(df))
        with col2:
            st.metric("Total de Colunas", len(df.columns))
        with col3:
            colunas_quantidade = [col for col in df.columns if col.startswith(('6F', '8F'))]
            st.metric("Colunas de Quantidade", len(colunas_quantidade))
    
    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_plaquetas = df['QUANTIDADE_TOTAL'].sum()
    total_vendas = len(df)
    total_clientes = df['CLIENTE'].nunique()
    total_estados = df['UF'].nunique()
    
    with col1:
        st.metric("Total de Plaquetas", f"{total_plaquetas:,.0f}")
    with col2:
        st.metric("Total de Vendas", f"{total_vendas:,}")
    with col3:
        st.metric("Clientes Únicos", f"{total_clientes:,}")
    with col4:
        st.metric("Estados Atendidos", f"{total_estados}")
    
    # Resposta em destaque
    vendas_regiao = calcular_vendas_por_regiao(df)
    top_regiao = vendas_regiao.iloc[0]
    
    st.markdown(f"""
    <div class="resposta-destaque">
        <h2>🎯 Quais são as regiões que mais vendem?</h2>
        <h3>🥇 {top_regiao['REGIAO']}: {top_regiao['Quantidade']:,.0f} plaquetas ({top_regiao['Percentual']}%)</h3>
        <p>A região {top_regiao['REGIAO']} lidera com quase metade das vendas totais!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Vendas por Região")
        fig_regiao = px.bar(
            vendas_regiao,
            x='REGIAO',
            y='Quantidade',
            color='Quantidade',
            color_continuous_scale='Reds',
            title="Quantidade de Plaquetas por Região",
            text='Quantidade'
        )
        fig_regiao.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_regiao.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_regiao, use_container_width=True)
    
    with col2:
        st.subheader("🥧 Distribuição Regional")
        fig_pie = px.pie(
            vendas_regiao,
            values='Quantidade',
            names='REGIAO',
            title="Participação das Regiões nas Vendas",
            color_discrete_sequence=px.colors.sequential.Reds_r
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Top estados
    st.subheader("🏆 Top 10 Estados")
    vendas_estado = df.groupby('UF').agg({
        'QUANTIDADE_TOTAL': 'sum',
        'CLIENTE': 'nunique',
        'DATA': 'count'
    }).rename(columns={
        'QUANTIDADE_TOTAL': 'Quantidade',
        'CLIENTE': 'Clientes',
        'DATA': 'Vendas'
    }).reset_index().sort_values('Quantidade', ascending=False).head(10)
    
    vendas_estado['Percentual'] = (vendas_estado['Quantidade'] / total_plaquetas * 100).round(1)
    
    fig_estados = px.bar(
        vendas_estado,
        x='UF',
        y='Quantidade',
        color='Quantidade',
        color_continuous_scale='Blues',
        title="Top 10 Estados por Quantidade de Plaquetas",
        text='Quantidade',
        hover_data=['Clientes', 'Vendas', 'Percentual']
    )
    fig_estados.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_estados.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig_estados, use_container_width=True)
    
    # Mapa de calor dos estados
    st.subheader("🗺️ Mapa de Calor - Vendas por Estado")
    
    # Criar dados para o mapa de calor
    vendas_completo = df.groupby('UF')['QUANTIDADE_TOTAL'].sum().reset_index()
    vendas_completo['Intensidade'] = pd.cut(
        vendas_completo['QUANTIDADE_TOTAL'], 
        bins=5, 
        labels=['Muito Baixo', 'Baixo', 'Médio', 'Alto', 'Muito Alto']
    )
    
    # Exibir tabela interativa
    st.dataframe(
        vendas_completo.sort_values('QUANTIDADE_TOTAL', ascending=False),
        column_config={
            "UF": "Estado",
            "QUANTIDADE_TOTAL": st.column_config.NumberColumn(
                "Quantidade Total",
                format="%d"
            ),
            "Intensidade": "Nível de Vendas"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Análise temporal
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Vendas por Mês")
        # Filtrar apenas dados com mês válido
        df_mes_valido = df[df['MES'].notna()].copy()
        
        if not df_mes_valido.empty:
            vendas_mes = df_mes_valido.groupby('MES')['QUANTIDADE_TOTAL'].sum().reset_index()
            meses_nomes = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
                          7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
            vendas_mes['MES_NOME'] = vendas_mes['MES'].map(meses_nomes)
            
            fig_mes = px.line(
                vendas_mes,
                x='MES_NOME',
                y='QUANTIDADE_TOTAL',
                title="Evolução das Vendas Mensais",
                markers=True,
                line_shape='spline'
            )
            fig_mes.update_layout(height=400)
            st.plotly_chart(fig_mes, use_container_width=True)
        else:
            st.warning("Dados de mês não disponíveis")
    
    # Top clientes e análise de consultores
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Top 10 Clientes")
        top_clientes = df.groupby('CLIENTE')['QUANTIDADE_TOTAL'].sum().sort_values(ascending=False).head(10)
        
        fig_clientes = px.bar(
            x=top_clientes.values,
            y=top_clientes.index,
            orientation='h',
            title="Maiores Clientes por Volume",
            color=top_clientes.values,
            color_continuous_scale='Greens'
        )
        fig_clientes.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_clientes, use_container_width=True)
    
    with col2:
        st.subheader("👨‍💼 Top 10 Consultores")
        # Filtrar apenas consultores válidos (não nulos/vazios)
        df_consultores = df[df['CONSULTOR'].notna() & (df['CONSULTOR'].str.strip() != '')].copy()
        
        if not df_consultores.empty:
            top_consultores = df_consultores.groupby('CONSULTOR')['QUANTIDADE_TOTAL'].sum().sort_values(ascending=False).head(10)
            
            fig_consultores = px.bar(
                x=top_consultores.values,
                y=top_consultores.index,
                orientation='h',
                title="Consultores com Maior Volume de Vendas",
                color=top_consultores.values,
                color_continuous_scale='Blues'
            )
            fig_consultores.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_consultores, use_container_width=True)
        else:
            st.warning("Dados de consultores não disponíveis")
    
    # Análise de modelos
    st.subheader("🔧 Análise por Modelo de Plaqueta")
    
    # Calcular vendas por modelo (6F vs 8F) de forma mais robusta
    colunas_6f = [col for col in df.columns if '6F' in col and df[col].dtype in ['int64', 'float64']]
    colunas_8f = [col for col in df.columns if '8F' in col and df[col].dtype in ['int64', 'float64']]
    
    # Garantir que temos dados numéricos
    vendas_6f = 0
    vendas_8f = 0
    
    if colunas_6f:
        vendas_6f = df[colunas_6f].fillna(0).sum().sum()
    if colunas_8f:
        vendas_8f = df[colunas_8f].fillna(0).sum().sum()
    
    # Evitar divisão por zero
    total_modelos = vendas_6f + vendas_8f
    
    if total_modelos > 0:
        modelos_data = pd.DataFrame({
            'Modelo': ['6 Furos', '8 Furos'],
            'Quantidade': [int(vendas_6f), int(vendas_8f)],
            'Percentual': [
                (vendas_6f/total_modelos)*100, 
                (vendas_8f/total_modelos)*100
            ]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_modelos = px.bar(
                modelos_data,
                x='Modelo',
                y='Quantidade',
                color='Modelo',
                title="Vendas por Modelo de Plaqueta",
                text='Quantidade',
                color_discrete_map={'6 Furos': '#3498db', '8 Furos': '#e74c3c'}
            )
            fig_modelos.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_modelos, use_container_width=True)
        
        with col2:
            st.metric("Modelo 6 Furos", f"{int(vendas_6f):,.0f}", f"{modelos_data.iloc[0]['Percentual']:.1f}%")
            st.metric("Modelo 8 Furos", f"{int(vendas_8f):,.0f}", f"{modelos_data.iloc[1]['Percentual']:.1f}%")
            
            modelo_preferido = "6 Furos" if vendas_6f > vendas_8f else "8 Furos"
            st.success(f"🏆 Modelo mais vendido: **{modelo_preferido}**")
    else:
        st.warning("Dados de modelos não disponíveis ou inválidos")
    
    # === SEÇÃO COMPLETA DE ANÁLISE DE VENDEDORES/CONSULTORES ===
    st.header("👨‍💼 Análise Detalhada dos Consultores")
    
    # Filtrar dados válidos de consultores
    df_consultores = df[df['CONSULTOR'].notna() & (df['CONSULTOR'].str.strip() != '')].copy()
    
    if not df_consultores.empty:
        # KPIs dos consultores
        total_consultores = df_consultores['CONSULTOR'].nunique()
        vendas_por_consultor = df_consultores.groupby('CONSULTOR').agg({
            'QUANTIDADE_TOTAL': ['sum', 'count', 'mean'],
            'CLIENTE': 'nunique',
            'UF': 'nunique'
        }).round(0)
        
        # Flatten column names
        vendas_por_consultor.columns = ['Total_Plaquetas', 'Num_Vendas', 'Ticket_Medio', 'Clientes_Unicos', 'Estados_Atendidos']
        vendas_por_consultor = vendas_por_consultor.reset_index()
        vendas_por_consultor = vendas_por_consultor.sort_values('Total_Plaquetas', ascending=False)
        
        # Métricas gerais dos consultores
        st.subheader("📊 Métricas Gerais da Equipe")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Consultores", total_consultores)
        with col2:
            media_vendas = vendas_por_consultor['Total_Plaquetas'].mean()
            st.metric("Média por Consultor", f"{media_vendas:,.0f}")
        with col3:
            top_performer = vendas_por_consultor.iloc[0]
            st.metric("Top Performer", top_performer['CONSULTOR'])
        with col4:
            participacao_top = (top_performer['Total_Plaquetas'] / df_consultores['QUANTIDADE_TOTAL'].sum() * 100)
            st.metric("% do Top Performer", f"{participacao_top:.1f}%")
        
        # Ranking detalhado dos consultores
        st.subheader("🏆 Ranking Completo dos Consultores")
        
        # Adicionar ranking e performance
        vendas_por_consultor['Ranking'] = range(1, len(vendas_por_consultor) + 1)
        vendas_por_consultor['Performance'] = pd.cut(
            vendas_por_consultor['Total_Plaquetas'], 
            bins=3, 
            labels=['🟡 Básico', '🟠 Bom', '🟢 Excelente']
        )
        
        # Tabela interativa
        st.dataframe(
            vendas_por_consultor[['Ranking', 'CONSULTOR', 'Total_Plaquetas', 'Num_Vendas', 
                                'Ticket_Medio', 'Clientes_Unicos', 'Estados_Atendidos', 'Performance']],
            column_config={
                "Ranking": st.column_config.NumberColumn("🏆 Rank", format="%d"),
                "CONSULTOR": "👨‍💼 Consultor",
                "Total_Plaquetas": st.column_config.NumberColumn("📦 Total Plaquetas", format="%d"),
                "Num_Vendas": st.column_config.NumberColumn("🔢 Nº Vendas", format="%d"),
                "Ticket_Medio": st.column_config.NumberColumn("💰 Ticket Médio", format="%.0f"),
                "Clientes_Unicos": st.column_config.NumberColumn("👥 Clientes", format="%d"),
                "Estados_Atendidos": st.column_config.NumberColumn("🗺️ Estados", format="%d"),
                "Performance": "⭐ Performance"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Gráficos de análise dos consultores
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Volume vs Número de Vendas")
            fig_scatter = px.scatter(
                vendas_por_consultor,
                x='Num_Vendas',
                y='Total_Plaquetas',
                size='Clientes_Unicos',
                color='Performance',
                hover_name='CONSULTOR',
                title="Eficiência dos Consultores",
                labels={
                    'Num_Vendas': 'Número de Vendas',
                    'Total_Plaquetas': 'Total de Plaquetas',
                    'Clientes_Unicos': 'Clientes Únicos'
                }
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Distribuição de Performance")
            performance_count = vendas_por_consultor['Performance'].value_counts()
            
            fig_performance = px.pie(
                values=performance_count.values,
                names=performance_count.index,
                title="Distribuição de Performance da Equipe",
                color_discrete_map={
                    '🟢 Excelente': '#27ae60',
                    '🟠 Bom': '#f39c12', 
                    '🟡 Básico': '#f1c40f'
                }
            )
            st.plotly_chart(fig_performance, use_container_width=True)
        
        # Análise de eficiência
        st.subheader("⚡ Análise de Eficiência")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Consultor mais eficiente (maior ticket médio)
            mais_eficiente = vendas_por_consultor.loc[vendas_por_consultor['Ticket_Medio'].idxmax()]
            st.info(f"""
            **🎯 Maior Ticket Médio**
            
            👨‍💼 {mais_eficiente['CONSULTOR']}
            
            💰 {mais_eficiente['Ticket_Medio']:,.0f} plaquetas/venda
            """)
        
        with col2:
            # Consultor com mais diversidade de clientes
            mais_diverso = vendas_por_consultor.loc[vendas_por_consultor['Clientes_Unicos'].idxmax()]
            st.warning(f"""
            **🌟 Maior Diversidade**
            
            👨‍💼 {mais_diverso['CONSULTOR']}
            
            👥 {mais_diverso['Clientes_Unicos']} clientes únicos
            """)
        
        with col3:
            # Consultor com maior abrangência geográfica
            mais_abrangente = vendas_por_consultor.loc[vendas_por_consultor['Estados_Atendidos'].idxmax()]
            st.success(f"""
            **🗺️ Maior Abrangência**
            
            👨‍💼 {mais_abrangente['CONSULTOR']}
            
            📍 {mais_abrangente['Estados_Atendidos']} estados atendidos
            """)
        
        # Análise temporal dos consultores
        st.subheader("📅 Performance Temporal dos Consultores")
        
        # Vendas por consultor por mês
        df_tempo_consultor = df_consultores[df_consultores['MES'].notna()].copy()
        
        if not df_tempo_consultor.empty:
            vendas_mes_consultor = df_tempo_consultor.groupby(['MES', 'CONSULTOR'])['QUANTIDADE_TOTAL'].sum().reset_index()
            
            # Pegar apenas top 5 consultores para não poluir o gráfico
            top5_consultores = vendas_por_consultor.head(5)['CONSULTOR'].tolist()
            vendas_mes_top5 = vendas_mes_consultor[vendas_mes_consultor['CONSULTOR'].isin(top5_consultores)]
            
            meses_nomes = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
                          7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
            vendas_mes_top5['MES_NOME'] = vendas_mes_top5['MES'].map(meses_nomes)
            
            fig_temporal = px.line(
                vendas_mes_top5,
                x='MES_NOME',
                y='QUANTIDADE_TOTAL',
                color='CONSULTOR',
                title="Evolução Mensal - Top 5 Consultores",
                markers=True,
                line_shape='spline'
            )
            fig_temporal.update_layout(height=400)
            st.plotly_chart(fig_temporal, use_container_width=True)
        
        # Insights sobre consultores
        st.subheader("💡 Insights da Equipe de Vendas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Estatísticas da equipe
            st.info(f"""
            **📊 Estatísticas da Equipe**
            
            • **Média de vendas:** {vendas_por_consultor['Num_Vendas'].mean():.1f} vendas/consultor
            • **Mediana de plaquetas:** {vendas_por_consultor['Total_Plaquetas'].median():,.0f}
            • **Desvio padrão:** {vendas_por_consultor['Total_Plaquetas'].std():,.0f}
            • **Amplitude:** {vendas_por_consultor['Total_Plaquetas'].max() - vendas_por_consultor['Total_Plaquetas'].min():,.0f}
            """)
        
        with col2:
            # Recomendações
            st.success(f"""
            **🎯 Recomendações**
            
            • **Benchmarking:** Analisar práticas do top performer
            • **Treinamento:** Focar em consultores com performance básica
            • **Incentivos:** Criar metas baseadas em ticket médio
            • **Territórios:** Redistribuir regiões para maior eficiência
            """)
            
    else:
        st.warning("⚠️ Dados de consultores não disponíveis para análise detalhada.")
    
    # Insights finais
    st.subheader("💡 Principais Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **Região Líder**
        
        🥇 {vendas_regiao.iloc[0]['REGIAO']} domina com {vendas_regiao.iloc[0]['Percentual']}% das vendas
        
        📊 {vendas_regiao.iloc[0]['Quantidade']:,.0f} plaquetas vendidas
        """)
    
    with col2:
        estado_lider = vendas_estado.iloc[0]
        st.warning(f"""
        **Estado Campeão**
        
        🏆 {estado_lider['UF']} lidera com {estado_lider['Percentual']}%
        
        👥 {estado_lider['Clientes']} clientes únicos
        """)
    
    with col3:
        ticket_medio = total_plaquetas / total_vendas
        if not df_consultores.empty:
            melhor_consultor = vendas_por_consultor.iloc[0]['CONSULTOR']
            st.success(f"""
            **Performance Geral**
            
            📈 Ticket médio: {ticket_medio:.0f} plaquetas/venda
            
            🌟 Top consultor: {melhor_consultor}
            """)
        else:
            st.success(f"""
            **Performance Geral**
            
            📈 Ticket médio: {ticket_medio:.0f} plaquetas/venda
            
            🎯 {total_clientes} clientes em {total_estados} estados
            """)

if __name__ == "__main__":
    main()