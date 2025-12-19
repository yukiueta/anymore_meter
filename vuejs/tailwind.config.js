const primaryColors = require('@left4code/tw-starter/dist/js/colors')

module.exports = {
  mode: "jit",
  purge: [
    './src/**/*.{php,html,js,jsx,ts,tsx,vue}',
    './resources/**/*.{php,html,js,jsx,ts,tsx,vue}',
    './node_modules/@left4code/tw-starter/**/*.js'
  ],
  darkMode: 'class',
  theme: {
    borderColor: theme => ({
      ...theme('colors'),
      DEFAULT: primaryColors.gray['300']
    }),
    fontSize: {
      'xxs': ['0.3rem', '0.6rem'],
      'xs': ['0.5rem', '0.75rem'],
      'sm': ['0.8rem', '1.05rem'],
      'base': ['1rem', '1.25rem'],
      'lg': ['1.1rem', '1.35rem'],
      'xl': ['1.25rem', '1.5rem'],
      '2xl': ['1.563rem', '1.80rem'],
      '3xl': ['1.953rem', '2.20rem'],
      '4xl': ['2.441rem', '2.75rem'],
      '5xl': ['3.052rem', '3.25rem'],
    },
    colors: {
      ...primaryColors,
      primary: {
        ...primaryColors.primary,
        12: '#00428C',
      },
      dark: {
        ...primaryColors.dark,
        8: '#242b3c'
      },
      white: 'white',
      black: 'black',
      hover: '#EFF6FF',
      current: 'current',
      transparent: 'transparent',
      theme: {
        1: '#071A50',
        2: '#2D427B',
        3: '#A2AFD5',
        4: '#C6D4FD',
        5: '#D32929',
        6: '#365A74',
        7: '#D2DFEA',
        8: '#7F9EB8',
        9: '#008BF2',
        10: '#13B176',
        11: '#11296d',
        12: '#00428C',
        13: '#9BADE4',
        14: '#1c3271',
        15: '#F1F5F8',
        16: '#102867',
        17: '#142E71',
        18: '#172F71',
        19: '#B2BEDE',
        20: '#102765',
        21: '#3160D8',
        22: '#F78B00',
        23: '#FBC500',
        24: '#CE3131',
        25: '#E2EBF2',
        26: '#203f90',
        27: '#8DA9BE',
        28: '#607F96',
        29: '#B8F1E1',
        30: '#FFE7D9',
        31: '#DBDFF9',
        32: '#2B4286',
        33: '#8C9DCA',
        34: '#0E2561',
        35: '#E63B1F'
      }
    },
    extend: {
      fontFamily: {
        roboto: ['Roboto']
      },
      container: {
        center: true
      },
      maxWidth: {
        '1/4': '25%',
        '1/2': '50%',
        '3/4': '75%'
      },
      strokeWidth: {
        0.5: 0.5,
        1.5: 1.5,
        2.5: 2.5
      }
    }
  },
  variants: {
    extend: {
      boxShadow: ['dark']
    }
  }
}
