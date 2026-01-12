import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DiffViewer from './DiffViewer.vue'

describe('DiffViewer', () => {
  it('should render diff content', () => {
    const content = `@@ -1,3 +1,4 @@
 line 1
+added line
 line 2
-removed line
 line 3`

    const wrapper = mount(DiffViewer, {
      props: {
        content,
        language: 'python',
      },
    })

    expect(wrapper.text()).toContain('line 1')
    expect(wrapper.text()).toContain('added line')
    expect(wrapper.text()).toContain('removed line')
  })

  it('should apply correct classes for added lines', () => {
    const content = `@@ -1,1 +1,2 @@
 context
+added`

    const wrapper = mount(DiffViewer, {
      props: { content },
    })

    const addedLine = wrapper.findAll('div').find((el) =>
      el.text().includes('added') && el.classes().some((c) => c.includes('green'))
    )
    expect(addedLine).toBeDefined()
  })

  it('should apply correct classes for removed lines', () => {
    const content = `@@ -1,2 +1,1 @@
 context
-removed`

    const wrapper = mount(DiffViewer, {
      props: { content },
    })

    const removedLine = wrapper.findAll('div').find((el) =>
      el.text().includes('removed') && el.classes().some((c) => c.includes('red'))
    )
    expect(removedLine).toBeDefined()
  })
})
