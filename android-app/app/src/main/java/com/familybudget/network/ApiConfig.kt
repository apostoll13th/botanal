package com.familybudget.network

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * API Configuration
 *
 * IMPORTANT: Update BASE_URL with your server's IP address
 *
 * For local development:
 * - If using Android Emulator: http://10.0.2.2:5000/api/
 * - If using physical device: http://YOUR_COMPUTER_IP:5000/api/
 *
 * For production:
 * - http://YOUR_SERVER_IP:5000/api/
 * - https://yourdomain.com/api/
 */
object ApiConfig {
    // TODO: Replace with your actual server URL
    const val BASE_URL = "http://10.0.2.2:5000/api/"

    private var authToken: String? = null

    fun setAuthToken(token: String?) {
        authToken = token
    }

    fun getAuthToken(): String? = authToken

    private val authInterceptor = Interceptor { chain ->
        val requestBuilder = chain.request().newBuilder()

        // Add authorization header if token exists
        authToken?.let {
            requestBuilder.addHeader("Authorization", "Bearer $it")
        }

        chain.proceed(requestBuilder.build())
    }

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    val apiService: ApiService by lazy {
        retrofit.create(ApiService::class.java)
    }
}
