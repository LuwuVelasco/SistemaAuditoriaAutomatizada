import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  updateProfile,
  onAuthStateChanged,
  updateEmail,
  updatePassword
} from 'firebase/auth'
import { doc, setDoc, getDoc, updateDoc } from 'firebase/firestore'
import { auth, db } from '../firebase'
import { mockUser } from '../data/mock'

const USE_MOCK = import.meta.env.VITE_FIREBASE_API_KEY === undefined
                 || import.meta.env.VITE_FIREBASE_API_KEY === 'your_firebase_api_key'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(USE_MOCK ? mockUser : null)
  const loading = ref(!USE_MOCK)
  const error = ref(null)

  const isAuthenticated = computed(() => !!user.value)
  const initials = computed(() => {
    if (!user.value?.name) return '?'
    return user.value.name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
  })

  if (!USE_MOCK) {
    onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        const snap = await getDoc(doc(db, 'users', firebaseUser.uid))
        if (snap.exists()) {
          user.value = { uid: firebaseUser.uid, ...snap.data() }
        } else {
          user.value = {
            uid: firebaseUser.uid,
            name: firebaseUser.displayName || 'Usuario',
            email: firebaseUser.email,
            createdAt: new Date().toISOString().split('T')[0],
            stats: { audits: 0, approvedFindings: 0 }
          }
        }
      } else {
        user.value = null
      }
      loading.value = false
    })
  }

  async function login(email, password) {
    error.value = null
    if (USE_MOCK) {
      user.value = { ...mockUser, email }
      return
    }
    const cred = await signInWithEmailAndPassword(auth, email, password)
    const snap = await getDoc(doc(db, 'users', cred.user.uid))
    if (snap.exists()) user.value = { uid: cred.user.uid, ...snap.data() }
  }

  async function signup(name, email, password) {
    error.value = null
    if (USE_MOCK) {
      user.value = { uid: 'mock-' + Date.now(), name, email, createdAt: new Date().toISOString().split('T')[0], stats: { audits: 0, approvedFindings: 0 } }
      return
    }
    const cred = await createUserWithEmailAndPassword(auth, email, password)
    await updateProfile(cred.user, { displayName: name })
    const userData = { name, email, createdAt: new Date().toISOString().split('T')[0], stats: { audits: 0, approvedFindings: 0 } }
    await setDoc(doc(db, 'users', cred.user.uid), userData)
    user.value = { uid: cred.user.uid, ...userData }
  }

  async function logout() {
    if (!USE_MOCK) await signOut(auth)
    user.value = null
  }

  async function updateUserProfile(data) {
    if (USE_MOCK) { user.value = { ...user.value, ...data }; return }
    await updateDoc(doc(db, 'users', user.value.uid), data)
    user.value = { ...user.value, ...data }
    if (data.name) await updateProfile(auth.currentUser, { displayName: data.name })
  }

  async function changePassword(newPassword) {
    if (USE_MOCK) return
    await updatePassword(auth.currentUser, newPassword)
  }

  return { user, loading, error, isAuthenticated, initials, login, signup, logout, updateUserProfile, changePassword }
})
