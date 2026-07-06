
export function getRole() {
    try {
        const user = JSON.parse(localStorage.getItem('user_me') || '{}')
        return user.role || 'commercial'
    } catch {
        return 'commercial'
    }
}

export function isReadOnly() {
    const role = getRole()
    // "lecture_seule" is the backend role string
    return role === 'lecture_seule'
}
