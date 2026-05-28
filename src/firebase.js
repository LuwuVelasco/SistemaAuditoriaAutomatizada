import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'

const firebaseConfig = {
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId:             import.meta.env.VITE_FIREBASE_APP_ID
}

function validateFirebaseConfig(config) {
  const placeholders = new Set([
    undefined,
    null,
    '',
    'your_firebase_api_key',
    'your_project.firebaseapp.com',
    'your_project_id',
    'your_project.firebasestorage.app',
    'your_sender_id',
    'your_app_id'
  ])

  const missing = Object.entries(config)
    .filter(([, value]) => placeholders.has(value))
    .map(([key]) => key)

  if (missing.length) {
    console.warn(
      `Firebase config incompleta o de ejemplo en el frontend: ${missing.join(', ')}. ` +
      'Si el deploy ya está en producción, rebuild con las variables reales del proyecto.'
    )
  }
}

validateFirebaseConfig(firebaseConfig)

const app = initializeApp(firebaseConfig)

export const auth = getAuth(app)
export const db   = getFirestore(app)
export default app
