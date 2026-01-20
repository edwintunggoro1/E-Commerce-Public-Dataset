import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os
import pandas as pd
import gdown
sns.set(style='dark')

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").item_value.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return bystate_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max", #mengambil tanggal order terakhir
        "order_id": "nunique",
        "item_value": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

FILE_ID = "17pDAE1NiwmxR5cjvRbTm0oi49CvAzgi-"
url = f"https://drive.google.com/uc?id={FILE_ID}"
output = "all_data.csv"

if not os.path.exists(output):
    gdown.download(url, output, quiet=False)

try:
    all_df = pd.read_csv(output)
except Exception:
    all_df = pd.read_csv(output, sep=";", encoding="utf-8", engine="python")

datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)
 
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()
 
with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://www.logohouse.org/images/ecommerce%20logo%20maker.png")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)


st.header('E-Commerce Dashboard :sparkles:')

st.subheader('Daily Orders')
 
col1, col2 = st.columns(2)
 
with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)
 
with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "USD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)
 
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
 
st.pyplot(fig)

st.subheader("Kategori Produk Terbanyak & Tersedikit Terjual")

# Ambil Top 5 Most & Least
top_5_most = sum_order_items_df.sort_values(by="item_value", ascending=False).head(5)
top_5_least = sum_order_items_df.sort_values(by="item_value", ascending=True).head(5)

# Buat 2 kolom
col1, col2 = st.columns(2)

# =========================
# Chart 1: Top 5 terbanyak
# =========================
with col1:
    st.markdown("### Top 5 Kategori Produk yang Paling Banyak Terjual")

    fig1, ax1 = plt.subplots(figsize=(8, 6))

    colors_most = ["red"] + ["lightblue"] * 4
    ax1.bar(top_5_most["product_category_name_english"], top_5_most["item_value"], color=colors_most)

    ax1.set_title("Top 5 Kategori Produk yang Paling Banyak Terjual")
    ax1.set_xlabel("Product Category")
    ax1.set_ylabel("Jumlah Order")
    ax1.tick_params(axis='x', rotation=45)
    plt.tight_layout()

    st.pyplot(fig1)

# =========================
# Chart 2: Top 5 tersedikit
# =========================
with col2:
    st.markdown("### Top 5 Kategori Produk yang Paling Sedikit Terjual")

    fig2, ax2 = plt.subplots(figsize=(8, 6))

    colors_least = ["red"] + ["lightblue"] * 4
    ax2.bar(top_5_least["product_category_name_english"], top_5_least["item_value"], color=colors_least)

    ax2.set_title("Top 5 Kategori Produk yang Paling Sedikit Terjual")
    ax2.set_xlabel("Product Category")
    ax2.set_ylabel("Jumlah Order")
    ax2.tick_params(axis='x', rotation=45)
    plt.tight_layout()

    st.pyplot(fig2)


st.subheader("Customer Demographics")
 
 
fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(
    x="customer_count", 
    y="customer_state",
    data=bystate_df.sort_values(by="customer_count", ascending=False),
    palette=colors,
    ax=ax
)
ax.set_title("Number of Customer by States", loc="center", fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 8))

colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]

sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, hue="customer_id", legend=False, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis ='x', labelsize=15, rotation=45)

sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, hue="customer_id", legend=False, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelsize=15, rotation=45)

sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, hue="customer_id", legend=False, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelsize=15, rotation=45)

plt.suptitle("Best Customer Based on RFM Parameters (customer_id)", fontsize=20)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
 
st.pyplot(fig)

st.subheader("Monthly Average Delivery Time Trend")

# Copy df agar aman tidak mengubah dataframe utama
df_orders = main_df.copy()

# Buat kolom delivery_time (dalam hari)
df_orders["delivery_time"] = (
    df_orders["order_delivered_customer_date"] - df_orders["order_purchase_timestamp"]
).dt.days

# Filter data yang delivery_time-nya valid
df_orders = df_orders.dropna(subset=["delivery_time"])
df_orders = df_orders[df_orders["delivery_time"] >= 0]

# Ekstrak tahun dan bulan
df_orders.loc[:, "order_purchase_year"] = df_orders["order_purchase_timestamp"].dt.year
df_orders.loc[:, "order_purchase_month"] = df_orders["order_purchase_timestamp"].dt.month

# Monthly average delivery time
monthly_avg_delivery_time = (
    df_orders.groupby(["order_purchase_year", "order_purchase_month"])["delivery_time"]
    .mean()
    .reset_index()
)

# Gabungkan year-month menjadi tanggal (awal bulan)
monthly_avg_delivery_time["order_date"] = pd.to_datetime(
    monthly_avg_delivery_time["order_purchase_year"].astype(str)
    + "-"
    + monthly_avg_delivery_time["order_purchase_month"].astype(str)
    + "-01"
)

# Sort agar garis tidak lompat-lompat
monthly_avg_delivery_time = monthly_avg_delivery_time.sort_values("order_date")

# Plot chart
fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(data=monthly_avg_delivery_time, x="order_date", y="delivery_time", ax=ax)
ax.set_title("Monthly Average Delivery Time Trend")
ax.set_xlabel("Date")
ax.set_ylabel("Average Delivery Time (Days)")
ax.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

st.pyplot(fig)
