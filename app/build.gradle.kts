import java.util.Properties
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

// Android 17 = API 37. CI passes the highest platform it can install (-Ptj.sdk=37).
val tjSdk = (project.findProperty("tj.sdk") as String?)?.toIntOrNull() ?: 36

val signProps = Properties().apply { val f = file("signing.properties"); if (f.exists()) f.inputStream().use { load(it) } }

android {
    namespace = "com.tomstechsolutions.jukebox"
    compileSdk = tjSdk

    defaultConfig {
        applicationId = "com.tomstechsolutions.jukebox"
        minSdk = 24
        targetSdk = tjSdk
        versionCode = 960
        versionName = "0.9.6-beta"
        vectorDrawables { useSupportLibrary = true }
    }

    signingConfigs {
        create("release") {
            storeFile = file("tomsjukebox.keystore")
            storePassword = signProps.getProperty("storePassword")
            keyAlias = signProps.getProperty("keyAlias")
            keyPassword = signProps.getProperty("keyPassword")
        }
    }
    // the signing key is unpacked by the workflow from app/signing.enc (secret SIGN_SECRET); without it local builds use the debug key
    val relSign = if (signProps.isEmpty) signingConfigs.getByName("debug") else signingConfigs.getByName("release")

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = relSign
        }
        debug { signingConfig = relSign }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
    buildFeatures { compose = true; buildConfig = true }
    packaging { resources { excludes += "/META-INF/{AL2.0,LGPL2.1}" } }
    lint { abortOnError = false; checkReleaseBuilds = false }
}

dependencies {
    val media3 = "1.8.0"
    implementation(platform("androidx.compose:compose-bom:2025.06.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.animation:animation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.9.1")
    implementation("androidx.media3:media3-exoplayer:$media3")
    implementation("androidx.media3:media3-exoplayer-hls:$media3")
    implementation("androidx.media3:media3-session:$media3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("com.google.guava:guava:33.4.0-android")
    implementation("androidx.work:work-runtime-ktx:2.10.1")
}
