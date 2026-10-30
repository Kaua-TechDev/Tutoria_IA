/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ['./app/templates/**/*.html'],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                base: {
                    900: '#0f1117',
                    800: '#171923',
                    700: '#1f2230',
                    600: '#2a2e3f',
                },
                accent: {
                    500: '#7c5cff',
                    400: '#9678ff',
                },
            },
        },
    },
};
